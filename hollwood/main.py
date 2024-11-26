import utils
import os
import torch
from openai import OpenAI
import agent
from tqdm import tqdm

os.environ["DASHSCOPE_API_KEY"] = "sk-5509cac262524fe49ead28608dd34c54"
### 超参数：模型名称，Hollmwood_prompt中的故事preliminiary
model_name='qwen-max'
# experiment_dir='./权力游戏test'
preliminary_story="守夜人威玛·罗伊斯爵士、威尔和盖瑞在长城以北追踪野人。威尔发现一群死去的野人，但当他们到达现场时，尸体已消失。罗伊斯遭遇神秘的异鬼，在一场短暂的战斗后被杀。威尔目睹了整个过程，最后被复活的罗伊斯掐住喉咙。"

### 生成角色设定，并迭代给editor修改
def test(experiment_dir,preliminary_story):
    Writer=agent.create_writer(model_name)
    Character_Design_First_Stage=agent.create_roles(Writer,preliminary_story)
    print("FIRST STAGE: "+Character_Design_First_Stage)
    Editor=agent.create_editor(model_name)
    Final_Character_Design=agent.iteration_writer_editor(Writer,Editor,Character_Design_First_Stage,1)
    print("FINAL:!!!!"+Final_Character_Design)
    # save the final character design for convenience of next stage experiment
    data={"Final_Character_Design":Final_Character_Design}
    path = experiment_dir+"/Character_Design.json"
    utils.save_json_file(path,data)
#test_2 for outline

def test_2(experiment_dir,preliminary_story):
    path_character_design = experiment_dir+"/Character_Design.json"
    Character_Design=utils.load_json_file(path_character_design)["Final_Character_Design"]
    
    Writer_outline=agent.outline_writer_agent(model_name)
    outline=agent.outline_formulation(Writer_outline,Character_Design,preliminary_story)
    #print(Character_Design)
    Editor=agent.create_editor_for_outline(model_name)
    print("*******First OUTline*****"+outline)
    Final_Outline=agent.iteration_outline_revise(preliminary_story,Writer_outline,Editor,outline,Character_Design,1)##change the iteration times here
    checked_Outline=agent.outline_format_check(Final_Outline,model_name)
    print("*******Final OUTline*****"+Final_Outline)
    print("*******checked OUTline*****"+checked_Outline)
    data={"./Final_Outline":Final_Outline,"checked_Outline":checked_Outline}
    
    path = experiment_dir+"/Outline.json"
    utils.save_json_file(path,data)
    return 0
#test_3 for story_expanded
def test_3(experiment_dir,preliminary_story):
    expanded_story_dict=agent.iterate_story_expanded_for_subplot(experiment_dir,model_name,n=2,preliminary_storyline=preliminary_story)
    path = experiment_dir+"/Expanded_Story.json"
    utils.save_json_file(path,expanded_story_dict)

def characters_extract(experiment_dir):
    path=experiment_dir+"/Character_Design.json"
    Character_Design=utils.load_json_file(path)["Final_Character_Design"]
    characters=utils.parse_character_design(Character_Design)  
    extracted_character_path=experiment_dir+"/Character_Design_Modified.json"
    utils.save_json_file(extracted_character_path,characters)
    
def plot_extracted(experiment_dir):
    outline_path=experiment_dir+"/Outline.json"
    characters_path=experiment_dir+"/Character_Design_Modified.json"
    characters_list=[]
    characters_dict=utils.load_json_file(characters_path) 
    for key,value in characters_dict.items():
        characters_list.append(value["full_name"])
        
    outline=utils.load_json_file(outline_path)["checked_Outline"]
    outline_modified=utils.parse_outline(outline,characters_list)
    path = experiment_dir+"/Outline_Modified.json"
    utils.save_json_file(path,outline_modified)
    
#test_4 for script draft
def test_4(experiment_dir,preliminary_story):
    Character_path=experiment_dir+"/Character_Design_Modified.json"
    Expanded_Story_path=experiment_dir+"/Expanded_Story.json"
    scripts=agent.script_generating(model_name,Character_path,Expanded_Story_path)
    utils.save_json_file(experiment_dir+"/scripts.json",scripts)
    # utils.save_json_file("./scripts.json",scripts)

#test_5 for actor_playing
def test_5(experiment_dir):
    Character_path=experiment_dir+"/Character_Design_Modified.json"
    scripts_path=experiment_dir+"/scripts.json"
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
    save_path=experiment_dir+"/Final_Screenplay.json"
    utils.save_json_file(save_path,Final_Screenplay)

# Character_path="Character_Design_Modified.json"
# scripts_path="scripts.json"
# save_path="./test_final.json"
# def test_6(experiment_dir):
#     Character_path=experiment_dir+"/Character_Design_Modified.json"
#     scripts_path=experiment_dir+"/scripts.json"
#     save_path=experiment_dir+"/test_final.json"
#     Final_Screenplay=agent.screenplay(Character_path,scripts_path)
#     utils.save_json_file(save_path,Final_Screenplay)

## 每次实验需要手动设置一个专门的文件夹存放结果，分阶段从上至下进行实验，每个阶段的结果都存放在对应的文件夹中

#目前所用的剧情概要是再hollmwood.py 的TEST_Prelimary中修改的，但每个函数都有剧情概要的接口，可以修改
#test 生成角色
#characters_extract(experiment_dir) 角色提取
#test_2(experiment_dir) 生成outline
#plot_extracted(experiment_dir) outline提取,这一步可能不成功的原因是生成格式不对，已经修改prompt并增加检查迭代，但还是有概率错误。
#test_3(experiment_dir) story扩写，该步时间较长，需要等待。
#test_4(experiment_dir) script draft
#test_5(experiment_dir) actor playing 生成最终剧本
def main():
    data=utils.load_json_file("权力的游戏.json")["plots"]
    logger=utils.get_logger("main")
    for idx,plot in tqdm(enumerate(data)):
        preliminary_story=plot["summary"]
        print(f"Experiment {idx} with preliminary story: {preliminary_story}")
        experiment_dir=f"./权力的游戏/{idx}"
        utils.create_dir(experiment_dir)
        try:
            test(experiment_dir,preliminary_story)
            characters_extract(experiment_dir)
            test_2(experiment_dir,preliminary_story)
            plot_extracted(experiment_dir)
            test_3(experiment_dir,preliminary_story)
            test_4(experiment_dir,preliminary_story)
            test_5(experiment_dir)
            logger.info(f"Experiment {idx} completed successfully")
        except Exception as e:
            print(f"Error in experiment {idx}: {e}")
            logger.error(f"Error in experiment {idx}: {e}")
            continue
        
    #experiment_dir="./权力的游戏"
    #utils.create_dir(experiment_dir)
    #test(experiment_dir)
    #characters_extract(experiment_dir)
    #test_2(experiment_dir)
    #plot_extracted(experiment_dir)
    #test_3(experiment_dir)
    #test_4(experiment_dir)
    #test_5(experiment_dir)
if __name__ == '__main__':
    main()