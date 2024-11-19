import utils
import os
import torch
from openai import OpenAI
import agent


model_name='qwen-max'

def test():
    Writer=agent.create_writer(model_name)
    Character_Design_First_Stage=agent.create_roles(Writer)
    print("FIRST STAGE: "+Character_Design_First_Stage)
    Editor=agent.create_editor(model_name)
    Final_Character_Design=agent.iteration_writer_editor(Writer,Editor,Character_Design_First_Stage,1)
    print("FINAL:!!!!"+Final_Character_Design)
    # save the final character design for convenience of next stage experiment
    data={"Final_Character_Design":Final_Character_Design}
    path = "./Character_Design.json"
    utils.save_json_file(path,data)
#test_2 for outline
def test_2():
    Character_Design=utils.load_json_file("./Character_Design.json")["Final_Character_Design"]
    
    Writer_outline=agent.outline_writer_agent(model_name)
    outline=agent.outline_formulation(Writer_outline,Character_Design)
    #print(Character_Design)
    Editor=agent.create_editor_for_outline(model_name)
    print("*******First OUTline*****"+outline)
    Final_Outline=agent.iteration_outline_revise(Writer_outline,Editor,outline,Character_Design,1)
    checked_Outline=agent.outline_format_check(Final_Outline,model_name)
    print("*******Final OUTline*****"+Final_Outline)
    print("*******checked OUTline*****"+checked_Outline)
    data={"./Final_Outline":Final_Outline,"checked_Outline":checked_Outline}
    path = "./Outline.json"
    utils.save_json_file(path,data)
    return 0
#test_3 for story_expanded
def test_3():
    agent.iterate_story_expanded_for_subplot(model_name)
    
#test_4 for script draft
def test_4():
    Character_path="Character_Design_Modified.json"
    Expanded_Story_path="Expanded_Story.json"
    scripts=agent.script_generating(model_name,Character_path,Expanded_Story_path)
    utils.save_json_file("./scripts.json",scripts)

#test_5 for actor_playing
def test_5():
    Character_path="Character_Design_Modified.json"
    scripts_path="scripts.json"
    roles=agent.create_roles_for_script_draft(model_name,Character_path)
    scripts=utils.load_json_file(scripts_path)
    Final_Screenplay={}
    for key,value in scripts.items():
        #if key=="plot_1b": break
        Events=agent.Event_split(value["script_draft"])
        involved_characters_introductions=agent.get_character_info(value["characters"],Character_path)
        history_dialog=[]
        plot_event={}
        for idx,event in enumerate(Events):
            detailed_performances=agent.Actor_Playing(event,roles,history_dialog=history_dialog,scene=value["scene"],involved_characters_introductions=involved_characters_introductions)
            print(f"history:{history_dialog}")
            print(detailed_performances)
            plot_event[idx]=detailed_performances
        Final_Screenplay[key]=plot_event
    utils.save_json_file("./Final_Screenplay.json",Final_Screenplay)

Character_path="Character_Design_Modified.json"
scripts_path="scripts.json"
save_path="./test_final.json"
def test_6():
    agent.screenplay(Character_path,scripts_path,save_path)


    
    
if __name__ == '__main__':
    test_6()
