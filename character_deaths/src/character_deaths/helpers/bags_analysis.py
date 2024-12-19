death_verbs_patient = {
    "kill", "murder", "execute", "assassinate", "slay",
    "behead", "crucify", "hang", "drown",
    "poison", "decapitate", "sacrifice", "eradicate",
    "annihilate", "exterminate", "obliterate", "destroy",
    "massacre", "euthanize", "lynch", "terminate"
}
    
death_verbs_agent = {
    "die", "commit", "perish", "sacrifice",
    "pass away", "expire", "succumb", 
    "surrender life", "bleed out"
}

def count_character_deaths(characters_bags):
    death_count = 0
    character_death_flags = {}
    
    for character in characters_bags:
        char_name = character['name']
        char_bag = character['bag']
        
        died = False
        
        for verb_type, verb in char_bag:
            if verb_type == 'patient verb' and verb in death_verbs_patient:
                died = True
                break
                
            if verb_type == 'agent verb' and verb in death_verbs_agent:
                died = True
                break
        
        character_death_flags[char_name] = 1 if died else 0
        
        if died:
            death_count += 1
    
    return death_count, character_death_flags