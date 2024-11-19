import os 
os.environ["DASHSCOPE_API_KEY"] = "sk-5509cac262524fe49ead28608dd34c54"
import utils
import hollmwood_prompt
import json
import torch
from tqdm import tqdm
import re
# 创建作家
## 第一阶段，创建角色，并交互editor进行revise
def create_writer(model_name):
    Writer = utils.get_models(model_name)
    #llm = get_model()

    Writer.initialize_message()
    # 输入系统设定
    Writer.system_message(hollmwood_prompt.WRITER_CREATE_ROLE_SYSTEM_PROMPT)
    # 输入角色创作prompt，插入prestoryline
    return Writer
def create_roles(Writer, preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE):
    # Writer.user_message(hollmwood_prompt.WRITER_CREATE_ROLE_USER_PROMPT.format(preliminary_storyline=preliminary_storyline))
    WRITER_CREATE_ROLE_USER_PROMPT=hollmwood_prompt.WRITER_CREATE_ROLE_USER_PROMPT.format(preliminary_storyline=preliminary_storyline)
    # Character_Design_First_Stage=Writer.get_response()
    Character_Design_First_Stage=Writer.chat(WRITER_CREATE_ROLE_USER_PROMPT)
    # Writer.ai_message(Character_Design_First_Stage)
    return Character_Design_First_Stage
    
def create_editor(model_name):
    Editor= utils.get_models(model_name)
    Editor.initialize_message()
    # 输入系统设定,该editor角色设定不需要preliminary_storyline
    Editor.system_message(hollmwood_prompt.EDITOR_CREATE_ROLE_SYSTEM_PROMPT)
    return Editor

def get_advice_character(Editor,Character_design,flag=True):
    # 填充preliminary_storyline和initial_characters_written_by_Writer
    Advise_prompt=""
    if (flag):
        # Editor.user_message
        Advise_prompt=(hollmwood_prompt.EDITOR_CREATE_ROLE_USER_PROMPT.format(preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE,initial_characters_written_by_Writer=Character_design))
    else:
        # Editor.user_message
        Advise_prompt=(hollmwood_prompt.EDITOR_FEEDBACK_SYSTEM_PROMPT.format(preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE,Writer_revised_characters=Character_design))
        
    Character_Design_Editor_Advise=Editor.chat(Advise_prompt)
    # Editor.ai_message(Character_Design_Editor_Advise)
    return Character_Design_Editor_Advise

def iteration_writer_editor(Writer,Editor,Character_design,n=1):
    # 第一步writer生成角色设定导入
    # 获取编辑建议
    Character_design_advice=get_advice_character(Editor,Character_design)
    
    print("Character_design_advice:"+Character_design_advice)
    
    #Writer.user_message
    Revised_Prompt=(hollmwood_prompt.WRITER_REVISE_CHARACTERS_USER_PROMPT.format(Editor_advice_on_characters=Character_design_advice,preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE,last_revision=Character_design))      
                     
    Revised_Character_Design=Writer.chat(Revised_Prompt)
    print("Revised_Character_Design:"+Revised_Character_Design)
    # Writer.ai_message(Revised_Character_Design)
    ## 以上是第一次迭代，由于prompt不完全相同 以下是后续迭代 n默认值为0
    for i in range(n):
        Character_design_advice=get_advice_character(Editor,Revised_Character_Design,False)
        print("Character_design_advice:{i}"+Character_design_advice)
        #Writer.user_message
        # 这里prompt添加上一版本的角色设定，否则输出格式可能不对，因为迭代所用的原prompt里没有显式的给出输出格式
        Revised_Prompt=(hollmwood_prompt.WRITER_REVISE_CHARACTERS_USER_PROMPT.format(Editor_advice_on_characters=Character_design_advice,preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE,last_revision=Revised_Character_Design))
        
        Revised_Character_Design=Writer.chat(Revised_Prompt)
        Writer.ai_message(Revised_Character_Design)
        
        Character_design=Revised_Character_Design
        print("Revised_Character_Design:{i}"+Revised_Character_Design)
        
    return Revised_Character_Design
## 第二阶段，创建outline，并交互editor进行revise
def outline_writer_agent(model_name):
    Writer= utils.get_models(model_name)
    Writer.initialize_message()
    # 输入系统设定
    Writer.system_message(hollmwood_prompt.WRITER_OUTLINE_SYSTEM_PROMPT)
    return Writer
def outline_formulation(Writer,Final_Characters_output):
    ## 第一次生成outline需要有system设定，否则输出格式不对
    # Outline_Prompt=hollmwood_prompt.WRITER_OUTLINE_SYSTEM_PROMPT+(hollmwood_prompt.WRITER_OUTLINE_USER_PROMPT.format(preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE,Final_Characters_output=Final_Characters_output))
    Outline_Prompt=(hollmwood_prompt.WRITER_OUTLINE_USER_PROMPT.format(preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE,Final_Characters_output=Final_Characters_output))    
    
    outline=Writer.chat(Outline_Prompt)
    return outline

def create_editor_for_outline(model_name):
    Editor= utils.get_models(model_name)
    Editor.initialize_message()
    # 输入系统设定,该editor角色设定不需要preliminary_storyline
    Editor.system_message(hollmwood_prompt.EDITOR_OUTLINE_SYSTEM_PROMPT)
    return Editor

def get_advise_outline(Editor,Character_Design,Outline,flag=True):
    if flag:
        advise_outline_prompt=(hollmwood_prompt.EDITOR_OUTLINE_USER_PROMPT.format(preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE,characters=Character_Design,Outline=Outline))
    else:
        advise_outline_prompt=(hollmwood_prompt.EDITOR_FEEDBACK_USER_PROMPT.format(preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE,characters=Character_Design,Writer_revised_outline=Outline))

    Editor_advice_on_outline=Editor.chat(advise_outline_prompt)
    return Editor_advice_on_outline

def iteration_outline_revise(Writer,Editor,Outline,Character_Design,n=1):
    advise_outline=get_advise_outline(Editor,Character_Design,Outline)
    revise_prompt=(hollmwood_prompt.WRITER_REVISE_OUTLINE_USER_PROMPT.format(Editor_advice_on_outline=advise_outline,preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE,last_revision=Outline))
    Revised_Outline=Writer.chat(revise_prompt)
    for i in range(n):
        Editor_advice_on_outline=get_advise_outline(Editor,Character_Design,Revised_Outline,False)
        print(f"Editor_advice_on_outline:{i}"+Editor_advice_on_outline)
        
        revise_prompt=(hollmwood_prompt.WRITER_REVISE_OUTLINE_USER_PROMPT.format(Editor_advice_on_outline=advise_outline,preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE,last_revision=Revised_Outline))
        Revised_Outline=Writer.chat(revise_prompt)
        print(f"Revised_Outline:{i}"+Revised_Outline)
    return Revised_Outline
        

def outline_format_check(outline,model_name):
    checker=utils.get_models(model_name)
    prompt="You should check the outline format, and give me the revised outline."+hollmwood_prompt.Outline_format+outline
    revised_outline=checker.chat(prompt)
    return revised_outline

def create_writer_for_story_expanded(model_name):
    Writer= utils.get_models(model_name)
    Writer.initialize_message()
    # 输入系统设定,该editor角色设定不需要preliminary_storyline
    Writer.system_message(hollmwood_prompt.WRITER_EXPAND_STORY_SYSTEM_PROMPT)
    return Writer

def Stroy_expanded(Writer,preliminary_storyline,Previous_Chapters,Scene,current_plot,characters,flag=False):
    flag_prompt=""
    if not flag: flag_prompt="." 
    else: flag_prompt=hollmwood_prompt.END_STROY_EXPANDED
    
    prompt=hollmwood_prompt.WRITER_EXPAND_STORY_USER_PROMPT.format(current_plot=current_plot,preliminary_storyline=preliminary_storyline,Previous_Chapters=Previous_Chapters,Scene=Scene,characters=characters,flag_prompt=flag_prompt)
    
    return Writer.chat(prompt)

def iterate_story_expanded_for_subplot(model_name,n=2,preliminary_storyline=hollmwood_prompt.TEST_PRELIMINARY_STORYLINE):
    # 读取Outline_Modified.json文件
    with open('Outline_Modified.json', 'r') as f:
        outline_data = json.load(f)
    
    # 初始化Writer
    Writer = create_writer_for_story_expanded(model_name)
    
    # 初始化Previous_Chapters为空列表
    Previous_Chapters = []
    
    # 初始化一个新的字典来存储展开的subplot
    expanded_story_dict = {}
    
    # 遍历每个plot
    for plot_key, plot_value in outline_data.items():
        if not plot_key[-1].isalpha():
            continue
        current_plot = plot_value["plot_text"]
                
        # 获取当前subplot的场景
        Scene = plot_value["scene"]
        characters=plot_value["characters"]
        Previous_Chapters_text="\n\n".join(Previous_Chapters)     
                # 调用Stroy_expanded函数展开当前subplot
        expanded_story = Stroy_expanded(Writer, preliminary_storyline, Previous_Chapters_text, Scene, current_plot, characters)
                
                # 更新Previous_Chapters，添加当前展开的subplot
        Previous_Chapters.append(expanded_story)
                
                # 如果Previous_Chapters的长度超过2，删除最旧的chapter
        if len(Previous_Chapters) > n:
            Previous_Chapters.pop(0)
                
                # 将展开的subplot添加到字典中
        expanded_story_dict[plot_key] = {
                    "scene": Scene,
                    "characters": characters,
                    "plot_content": current_plot,
                    "story_content": expanded_story
                }
        
        #break
    # 将字典写入新的json文件
    with open('Expanded_Story.json', 'w') as f:
        json.dump(expanded_story_dict, f, ensure_ascii=False, indent=4)

def create_writer_for_script_draft(model_name):
    Writer= utils.get_models(model_name)
    Writer.initialize_message()
    # 输入系统设定,该editor角色设定不需要preliminary_storyline
    Writer.system_message(hollmwood_prompt.WRITER_SCRIPT_DRAFT_SYSTEM_PROMPT)
    return Writer


def script_generating(model_name,Character_path,Expanded_Story_path):
    """_summary_
    Args:
        Writer (_type_):
        Character_path:导入角色，需要角色信息
        Expanded_Story_path:导入展开的story,story的角色去Character中找相应描述
    Returns:
        _type_:返回剧本
    """
    ## Data load
    Writer= create_writer_for_script_draft(model_name)
    Expanded_Story=utils.load_json_file(Expanded_Story_path)
    Characters=utils.load_json_file(Character_path)
    scripts={}
    
    for chapter_key, chapter_value in tqdm(Expanded_Story.items()):
        characters_info=[]
        # 获取当前章节的角色信息
        characters = chapter_value["characters"]
        scene=chapter_value["scene"]
        # 初始化章节剧本
        # chapter_script = ""       
        # 遍历当前章节的每个角色
        for character in characters:
            # 在角色json中找到相应的角色
            for key, value in Characters.items():
                if value["full_name"] == character:
                    # 获取角色信息
                    print(f"find character{character}")
                    character_info = value
                    characters_info.append(character_info)
        prompt=hollmwood_prompt.WRITER_SCRIPT_DRAFT_USER_PROMPT.format(story_chapter=chapter_value["story_content"],scene=scene, involved_characters_introductions=characters_info)
        
        script_draft_one_chapter=Writer.chat(prompt)
        scripts[chapter_key]={
            "scene": chapter_value["scene"],
            "characters": characters,
            "script_draft": script_draft_one_chapter
        }
        # scripts.append(script_draft_one_chapter)
        
    return scripts


def create_roles_for_script_draft(model_name, Character_path):
    Characters=utils.load_json_file(Character_path)
    roles={}
    for key, value in Characters.items():
        full_name=value["full_name"].lower()
        character_introduction=value["character_introduction"]
        prompt=hollmwood_prompt.ACTOR_SYSTEM_PROMPT.format(role_introduction=character_introduction,role_name=full_name)
        Writer= utils.get_models(model_name)
        Writer.system_message(prompt)
        roles[full_name]=Writer
    return roles
# roles 字典存储了agents，调用时根据名字查找

def Event_split(script_text):
    pattern = r'<character_performance>\s*<character>(.*?)</character>\s*<performance>(.*?)</performance>\s*</character_performance>'
    
    # 查找所有匹配的片段
    matches = re.findall(pattern, script_text, re.DOTALL)
    
    # 用于存储分割后的结果
    result = []
    
    # 遍历所有匹配到的角色与表现对
    for idx, (character, performance) in enumerate(matches):
        characters = [char.strip().lower() for char in character.split(',')]
        
        result.append({
            "character": characters,
            "performance": performance.strip()
        }) 
    
    return result

def Actor_Playing(performance_item,roles,history_dialog,scene,involved_characters_introductions):
    # 获取角色名字
    characters = performance_item["character"]
    detailed_performances = []
    for character in characters:
        # 在角色字典中找到相应的角色
        try:
            role_agent= roles[character]
        except:
            print(f"can not find {character}")
            continue
        prompt=hollmwood_prompt.ACTOR_USER_PROMPT.format(performance=performance_item["performance"],history_dialog=history_dialog,scene=scene,involved_characters_introductions=involved_characters_introductions)
        
        detailed_performance = role_agent.chat(prompt)
        
        dialog = character + extract_dialogue(detailed_performance) + "\n"
        
        history_dialog.append(dialog)

        detailed_performance={character: detailed_performance}
        detailed_performances.append(detailed_performance)
    return detailed_performances
     


test="""
<script_draft>\n<scene_heading>\nINT. AGRICULTURAL RESEARCH LAB - DAY\n</scene_heading>\n\n<character_performance>\n<character>Dr. Iris Hawke</character>\n<performance>Iris meticulously prepares her experimental setup, arranging petri dishes and test tubes with precision.</performance>\n</character_performance>\n\n<character_performance>\n<character>Dr. Elena Martinez</character>\n<performance>Elena stands by Iris, peering over the array of equipment. She looks at Iris with a mix of excitement and concern.</performance>\n</character_performance>\n\n<character_performance>\n<character>Dr. Elena Martinez</character>\n<performance>\"Iris, are you sure about this?\" Elena asks, her voice tinged with both excitement and worry.</performance>\n</character_performance>\n\n<character_performance>\n<character>Dr. Iris Hawke</character>\n<performance>Iris nods, her eyes gleaming with determination. \"Absolutely. We've run the simulations, and the theoretical models show that this method should work. If we can grow crops in Martian soil using irradiated water, it could be a game-changer for our food crisis.\"</performance>\n</character_performance>\n\n<character_performance>\n<character>Dr. Elena Martinez</character>\n<performance>Elena adjusts her glasses and smiles. \"Alright, let's get started then.\"</performance>\n</character_performance>\n\n<character_performance>\n<character>Dr. Iris Hawke, Dr. Elena Martinez</character>\n<performance>The two women begin the series of experiments, carefully measuring and mixing the irradiated water with the Martian soil. They plant seeds of wheat, potatoes, and lettuce, and monitor their growth under controlled conditions.</performance>\n</character_performance>\n\n<scene_heading>\nINT. AGRICULTURAL RESEARCH LAB - WEEKS LATER\n</scene_heading>\n\n<character_performance>\n<character>Dr. Amara Patel</character>\n<performance>Amara approaches Iris and Elena, her eyes wide with curiosity. \"These results are incredible, Iris. How did you manage to make it work so well?\"</performance>\n</character_performance>\n\n<character_performance>\n<character>Dr. Iris Hawke</character>\n<performance>Iris explains, detailing the precise combination of irradiated water and specific nutrients. \"It's all about finding the right balance. The irradiated water breaks down some of the toxic compounds in the soil, making it more hospitable for the plants.\"</performance>\n</character_performance>\n\n<character_performance>\n<character>Dr. Amara Patel</character>\n<performance>Amara nods, impressed. \"This could be the breakthrough we've been waiting for. I want to run some genetic tests on these plants to see if there are any mutations or adverse effects.\"</performance>\n</character_performance>\n\n<character_performance>\n<character>Dr. Iris Hawke</character>\n<performance>\"Please do,\" Iris replies, eager for further validation. \"We need to be absolutely sure before we scale this up.\"</performance>\n</character_performance>\n\n<scene_heading>\nINT. AGRICULTURAL RESEARCH LAB - EVENING\n</scene_heading>\n\n<character_performance>\n<character>Dr. Elena Martinez</character>\n<performance>Elena places a hand on Iris's shoulder as they review the latest data. \"You've done it, Iris. Your method is going to change everything. The colony, and maybe even humanity, owes you a debt of gratitude.\"</performance>\n</character_performance>\n\n<character_performance>\n<character>Dr. Iris Hawke</character>\n<performance>Iris feels a warm glow of pride and relief. \"It's a team effort, Elena. We're all in this together.\"</performance>\n</character_performance>\n\n<character_performance>\n<character>Dr. Iris Hawke, Dr. Elena Martinez</character>\n<performance>With the promising results and the unwavering support of their colleagues, Iris and Elena know they are one step closer to solving the food crisis and ensuring the survival of the Martian colony.</performance>\n</character_performance>\n</script_draft>"""

# result = Event_split(test)
# for key, value in result.items():
#     print(f"Entry {key}:")
#     print(f"  Character: {value['character']}")
#     print(f"  Performance: {value['performance']}\n")
    

      
def get_character_info(characters_list,Character_path):
    Characters=utils.load_json_file(Character_path)
    characters_info=[]
        # 获取当前章节的角色信息
    #characters = chapter_value["characters"]
    #scene=chapter_value["scene"]
        # 初始化章节剧本
        # chapter_script = ""       
        # 遍历当前章节的每个角色
    for character in characters_list:
            # 在角色json中找到相应的角色
        for key, value in Characters.items():
            if value["full_name"] == character:
                    # 获取角色信息
                print(f"find character{character}")
                character_info = value
                characters_info.append(character_info)
                
    return characters_info

# Character_Path="Character_Design_Modified.json"

# roles=create_roles_for_script_draft('qwen-max',Character_Path)
# print(roles)
# print(roles['Dr. Iris Hawke'].chat("who are you"))

import re

def extract_dialogue(detailed_performance):
    # 使用正则表达式查找<dialogue>标签中的内容
    match = re.search(r'<dialogue>(.*?)</dialogue>', detailed_performance, re.DOTALL)
    if match:
        print(f"find dialogue{match.group(1)}")
        return match.group(1).strip()
    else:
        print("No dialogue found.")
        return None

# 示例使用
# detailed_performance = '''<detailed_performance>
# <character>Dr. Elena Martinez</character>
# <action>Dr. Elena Martinez stands close to Dr. Iris Hawke, her eyes filled with a mix of excitement and concern.</action>
# <parenthetical>(with both excitement and worry, to Dr. Iris Hawke)</parenthetical>
# <dialogue>"Iris, are you sure about this?"</dialogue>
# </detailed_performance>'''

# dialogue = extract_dialogue(detailed_performance)
# print(dialogue)  # 输出: "Iris, are you sure about this?"

def screenplay(Character_path,scripts_path,save_path,model_name='qwen-max'):
    Character_path="Character_Design_Modified.json"
    scripts_path="scripts.json"
    roles=create_roles_for_script_draft(model_name,Character_path)
    scripts=utils.load_json_file(scripts_path)
    Final_Screenplay={}
    ## 遍历进度条为 plot
    for key,value in tqdm(scripts.items()) :
        Events=Event_split(value["script_draft"])
        involved_characters_introductions=get_character_info(value["characters"],Character_path)
        history_dialog=[]
        plot_event={}
        for idx,event in enumerate(Events):
            detailed_performances=Actor_Playing(event,roles,history_dialog=history_dialog,scene=value["scene"],involved_characters_introductions=involved_characters_introductions)
            print(f"history:{history_dialog}")
            print(detailed_performances)
            plot_event[idx]=detailed_performances
        #    break
        Final_Screenplay[key]=plot_event
       # break
    utils.save_json_file(save_path,Final_Screenplay)