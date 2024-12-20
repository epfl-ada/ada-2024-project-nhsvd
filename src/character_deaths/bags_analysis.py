# defined sets of verbs related to character deaths
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
    """
    count the number of characters who died and flag them accordingly.

    this function checks each character's verb associations to determine
    if they died, based on predefined sets of death-related verbs.

    parameters:
    - characters_bags: a list of dictionaries, each containing:
        - 'name': the character's name
        - 'bag': a list of tuples with verb type ('patient verb' or 'agent verb') and the verb itself

    returns:
    - death_count: total number of characters flagged as dead
    - character_death_flags: a dictionary mapping character names to 1 (dead) or 0 (alive)
    """
    death_count = 0
    character_death_flags = {}

    for character in characters_bags:
        char_name = character['name']
        char_bag = character['bag']

        died = False

        # check verbs in the character's bag of words for death-related verbs
        for verb_type, verb in char_bag:
            if verb_type == 'patient verb' and verb in death_verbs_patient:
                died = True
                break
            if verb_type == 'agent verb' and verb in death_verbs_agent:
                died = True
                break

        # flag the character as dead (1) or alive (0)
        character_death_flags[char_name] = 1 if died else 0

        # increment death count if the character is flagged as dead
        if died:
            death_count += 1

    return death_count, character_death_flags
