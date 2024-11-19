import os
# os.environ['http_proxy'] = "http://127.0.0.1:7890" 
# os.environ['https_proxy'] = "http://127.0.0.1:7890" 
import pickle
import json
import logging
import datetime
import re
import os
import torch


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def get_models(model_name):
    # return the combination of llm, embedding and tokenizer
    if model_name == 'openai':
        from modules.llm.LangChainGPT import LangChainGPT
        return LangChainGPT()
    elif model_name.startswith('gpt-3.5'):
        from modules.llm.LangChainGPT import LangChainGPT
        return LangChainGPT(model="gpt-3.5-turbo")
    elif model_name == 'gpt-4':
        from modules.llm.LangChainGPT import LangChainGPT
        return LangChainGPT(model="gpt-4")
    elif model_name == 'gpt-4-turbo':
        from modules.llm.LangChainGPT import LangChainGPT
        return LangChainGPT(model="gpt-4")
    elif model_name == 'gpt-4o':
        from modules.llm.LangChainGPT import LangChainGPT
        return LangChainGPT(model="gpt-4o")
    elif model_name.startswith('qwen'):
        from modules.llm.Qwen import Qwen
        return Qwen(model_name)
    elif "mistral" == model_name:
        from modules.llm.mistral import ChatMistral
        model = ChatMistral()
        return model
    else:
        print(f'Warning! undefined model {model_name}, use gpt-3.5-turbo instead.')
        from modules.llm.LangChainGPT import LangChainGPT
        return LangChainGPT()


def build_db(data, db_name, db_type, embedding):
    if True:
        from modules.db.ChromaDB import ChromaDB
        db = ChromaDB(embedding)
        db.init_from_data(data,db_name)
    return db

def get_root_dir():
    current_file_path = os.path.abspath(__file__)
    root_dir = os.path.dirname(current_file_path)
    return root_dir

def create_dir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def get_logger(experiment_name):
    logger = logging.getLogger(experiment_name)
    logger.setLevel(logging.INFO)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    create_dir(f"{get_root_dir()}/log/{experiment_name}")
    file_handler = logging.FileHandler(os.path.join(get_root_dir(),f"./log/{experiment_name}/{current_time}.log"),encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    # Avoid logging duplication
    logger.propagate = False

    return logger

def normalize_string(text):
    # 去除空格并将所有字母转为小写
    import re
    return re.sub(r'[\s\,\;\t\n]+', '', text).lower()

def fuzzy_match(str1, str2, threshold=0.8):
    str1_normalized = normalize_string(str1)
    str2_normalized = normalize_string(str2)

    if str1_normalized == str2_normalized:
        return True

    return False

def load_json_file(path):
    with open(path,"r",encoding="utf-8") as f:
        return json.load(f)
    
def load_jsonl_file(path):
    data = []
    with open(path,"r",encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data

def save_json_file(path,target):
    dir_name = os.path.dirname(path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    with open(path,"w",encoding="utf-8") as f:
        json.dump(target, f, ensure_ascii=False,indent=True)
        
def save_jsonl_file(path,target):
    with open(path, "w",encoding="utf-8") as f:
        for row in target:
            print(json.dumps(row, ensure_ascii=False), file=f)
    
def json_parser(output):
    output = output.replace("\n", "")
    output = output.replace("'", "\\'")
    output = output.replace("(", "（")
    output = output.replace(")", "）")    
    pattern = r'\{.*?\}'
    # 尝试匹配并提取 JSON 内容
    matches = re.findall(pattern, output, re.DOTALL)
    try:
        parsed_json = json.loads(matches[0])
        
    except json.JSONDecodeError:
        try:
            detail = re.search(r'"detail":\s*(.+?)\s*}', matches[0]).group(1)
            detail = f"\"{detail}\"" 
            new_output = re.sub(r'"detail":\s*(.+?)\s*}', f"\"detail\":{detail}}}", matches[0])
            parsed_json = json.loads(new_output)
        except Exception as e:
            raise ValueError("No valid JSON found in the input string")
    return parsed_json

def action_detail_decomposer(detail):
    thoughts = re.findall(r'【(.*?)】', detail)
    actions = re.findall(r'（(.*?)）', detail)
    dialogues = re.findall(r'「(.*?)」', detail)
    return thoughts,actions,dialogues

def conceal_thoughts(detail):
    return re.sub(r'【.*?】', '', detail)

def check_role_code_availability(role_code):
    for path in get_grandchild_folders("./data/roles"):
        if role_code in path:
            return True
    return False
    
def get_grandchild_folders(root_folder):
    folders = []
    for resource in os.listdir(root_folder):
        subpath = os.path.join(root_folder,resource)
        for folder_name in os.listdir(subpath):
            folder_path = os.path.join(subpath, folder_name)
            folders.append(folder_path)
    
    return folders
        
cache_sign = True
cache = None 
def cached(func):
	def wrapper(*args, **kwargs):	

		global cache
		cache_path = 'rpa_cache.pkl'
		if cache == None:
			if not os.path.exists(cache_path):
				cache = {}
			else:
				cache = pickle.load(open(cache_path, 'rb'))  

		key = ( func.__name__, str([args[0].role_name, args[0].__class__, args[0].llm_type , args[0].dialogue_history]), str(kwargs.items()))
		
		if (cache_sign and key in cache and cache[key] not in [None, '[TOKEN LIMIT]']) :
			return cache[key]
		else:
			
			result = func(*args, **kwargs)
			if result != 'busy' and result != None:
				cache[key] = result
				pickle.dump(cache, open(cache_path, 'wb'))
			return result

	return wrapper

# 解析字符串中的角色设计，拆分并存入Character_Design_Modified.json文件
def parse_character_design(input_text):
    # Regular expression patterns to match tags and content
    character_pattern = r"<character_\d+>(.*?)</character_\d+>"
    name_pattern = r"<full_name>(.*?)</full_name>"
    intro_pattern = r"<character_introduction>(.*?)</character_introduction>"

    # Dictionary to store all characters
    CHARACTER_DESIGN = {}

    # Find each character block
    character_blocks = re.findall(character_pattern, input_text, re.DOTALL)
    
    for i, block in enumerate(character_blocks, start=1):
        # Extract full name and introduction
        name_match = re.search(name_pattern, block)
        intro_match = re.search(intro_pattern, block)
        
        if name_match and intro_match:
            name = name_match.group(1)
            introduction = intro_match.group(1)
            
            # Store in CHARACTER_DESIGN dictionary
            CHARACTER_DESIGN[f"character_{i}"] = {
                "full_name": name,
                "character_introduction": introduction
            }

    return CHARACTER_DESIGN

# Character_Design=load_json_file("./Character_Design.json")["Final_Character_Design"]
# CHARACTER_DESIGN=parse_character_design(Character_Design)
# path = "./Character_Design_Modified.json"
# save_json_file(path,CHARACTER_DESIGN)

from collections import defaultdict

from collections import defaultdict

def parse_outline(text):
    # 定义要匹配的角色名单
    character_names = [
        "Dr. Iris Hawke", "Captain Leo Zhang", "Dr. Elena Martinez",
        "Samuel \"Sam\" Reed", "Dr. Amara Patel"
    ]
    
    # 提取人物的名字中的每个词，为匹配准备
    character_keywords = []
    for full_name in character_names:
        # 对每个名字拆解成单个词
        name_parts = re.split(r'\s|,', full_name)
        name_parts = [part.lower() for part in name_parts if part.lower() != 'dc']
        character_keywords.append((full_name, name_parts))

    # 使用字典存储结果，支持嵌套子级 plot
    result = defaultdict(dict)
    
    # 匹配所有 plot 的内容，包括有结束标签的和没有结束标签的
    plot_blocks = re.findall(r"(<plot_\d+[a-z]?>.*?</plot_\d+[a-z]?>|<plot_\d+[a-z]?>.*?)(?=<plot_\d+[a-z]?>|$)", text, re.DOTALL)

    for block in plot_blocks:
        if block.strip():  # 确保非空
            # 提取 plot_id（用非贪婪匹配）
            plot_id_match = re.match(r"<(plot_\d+[a-z]?)>", block)
            if plot_id_match:
                plot_id = plot_id_match.group(1)
                # 获取 plot 内容（不包括 Scene 和 Characters，若有的话）
                plot_text = block.replace(f"<{plot_id}>", "").strip()

                # 提取 scene 属性
                scene = ""
                scene_match = re.search(r"Scene:\s*(.*?)(?=\s*Characters:|$)", plot_text, re.DOTALL)
                scene = scene_match.group(1).strip() if scene_match else ""

                # 提取角色信息
                characters = []
                for full_name, name_parts in character_keywords:
                    # 检查 plot_text 中是否包含该角色的任何名字部分
                    if any(name_part in plot_text.lower() for name_part in name_parts):
                        characters.append(full_name)

                # 填充结果字典
                result[plot_id] = {
                    "plot_text": plot_text,
                    "scene": scene,
                    "characters": characters
                }

    return dict(result)


# Outline=load_json_file("./Outline.json")["checked_Outline"]
# Outline_modified=parse_outline(Outline)
# path = "./Outline_Modified.json"
# save_json_file(path,Outline_modified)