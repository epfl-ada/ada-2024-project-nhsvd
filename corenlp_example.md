# Example of CoreNLP processed data

**Movie ID: 9917462**

## Summary

"9917462 Sergeant Tom Clancy, of the North-West Mounted Police, is assigned to arrest his brother Steve, who has been framed for murder by "Black" McDougal and Pierre LaRue. {{Expand section}}"

## Characters

```
Character name			Freebase character ID
Inspector Cabot			/m/0bxrx7n
Sergeant Tom Clancy		/m/0bxrx5f
Ann Laurie				/m/0bxrx7d
Dave Moran				/m/0bxrx6k
Maureen Clancy			/m/0bxrx69
Steve Clancy			/m/0bxrx55
Constable McGregor		/m/0bxrx5p
Constable McIntosh		/m/0bxrx5_
Pierre LaRue			/m/0bxrx6w
Black McDougal			/m/0bxrx7z
```

## Tokens

```
sentence_id,token_id,word,lemma,CharacterOffsetBegin,CharacterOffsetEnd,POS,NER
1,1,Sergeant,sergeant,0,8,NN,O
1,2,Tom,Tom,9,12,NNP,PERSON
1,3,Clancy,Clancy,13,19,NNP,PERSON
1,4,",",",",19,20,",",O
1,5,of,of,21,23,IN,O
1,6,the,the,24,27,DT,O
1,7,North-West,North-West,28,38,NNP,ORGANIZATION
1,8,Mounted,Mounted,39,46,NNP,ORGANIZATION
1,9,Police,Police,47,53,NNP,ORGANIZATION
1,10,",",",",53,54,",",O
1,11,is,be,55,57,VBZ,O
1,12,assigned,assign,58,66,VBN,O
1,13,to,to,67,69,TO,O
1,14,arrest,arrest,70,76,VB,O
1,15,his,he,77,80,PRP$,O
1,16,brother,brother,81,88,NN,O
1,17,Steve,Steve,89,94,NNP,PERSON
1,18,",",",",94,95,",",O
1,19,who,who,96,99,WP,O
1,20,has,have,100,103,VBZ,O
1,21,been,be,104,108,VBN,O
1,22,framed,frame,109,115,VBN,O
1,23,for,for,116,119,IN,O
1,24,murder,murder,120,126,NN,O
1,25,by,by,127,129,IN,O
1,26,``,``,130,131,``,O
1,27,Black,black,131,136,JJ,O
1,28,'','',136,137,'',O
1,29,McDougal,mcdougal,138,146,NN,PERSON
1,30,and,and,147,150,CC,O
1,31,Pierre,Pierre,151,157,NNP,PERSON
1,32,LaRue,LaRue,158,163,NNP,PERSON
1,33,.,.,163,164,.,O
2,1,-LCB-,-lcb-,165,166,-LRB-,O
2,2,-LCB-,-lcb-,166,167,-LRB-,O
2,3,Expand,expand,167,173,VB,O
2,4,section,section,174,181,NN,O
2,5,-RCB-,-rcb-,181,182,-RRB-,O
2,6,-RCB-,-rcb-,182,183,-RRB-,O
```

## Dependencies

```
sentence_id,type,governor,governor_idx,dependent,dependent_idx
1,nn,Clancy,3,Sergeant,1
1,nn,Clancy,3,Tom,2
1,nsubjpass,assigned,12,Clancy,3
1,det,Police,9,the,6
1,nn,Police,9,North-West,7
1,nn,Police,9,Mounted,8
1,prep_of,Clancy,3,Police,9
1,auxpass,assigned,12,is,11
1,aux,arrest,14,to,13
1,xcomp,assigned,12,arrest,14
1,poss,brother,16,his,15
1,dobj,arrest,14,brother,16
1,tmod,arrest,14,Steve,17
1,nsubjpass,framed,22,who,19
1,aux,framed,22,has,20
1,auxpass,framed,22,been,21
1,rcmod,Steve,17,framed,22
1,prep_for,framed,22,murder,24
1,amod,McDougal,29,Black,27
1,agent,framed,22,McDougal,29
1,nn,LaRue,32,Pierre,31
1,agent,framed,22,LaRue,32
1,conj_and,McDougal,29,LaRue,32
2,prep,Expand,3,section,4
```

### Relevant dependencies expanded

```
Clancy	  ------(nn)-----> 	Sergeant
Clancy 	  ------(nn)-----> 	Tom
Clancy 	  --(nsubjpass)-->	assigned
Clancy 	  ---(prep_of)--->	Police
assigned  -----(xcomp)--->	arrest
brother	  -----(poss)---->	his
arrest	  -----(dobj)---->	brother
arrest	  -----(tmod)---->	Steve
Steve	  ----(rcmod)---->	framed
framed	  ---(prep_for)-->	murder
McDougal  -----(amod)---->	Black
framed	  ----(agent)---->	McDougal
LaRue	  ------(nn)----->	Pierre
framed	  ----(agent)---->	LaRue
McDougal  ---(conj_and)-->	LaRue
```

## Coreferences

```
representative,sentence_id,start,end,head
True,1,2,4,3
False,1,15,16,15
True,1,1,11,3
False,1,1,4,3
True,1,17,33,17
False,1,17,18,17
```

**Coreferences explained**

Format: `(sentence_id, head)  [start, end]`.

```
(1,3)  [2,4]		(Clancy) ["Tom", "Clancy", ","]
(1,15) [15,16]		(his)    ["his", "brother"]
```

```
(1,3) [1,11]		(Clancy) ["Sergeant", "Tom", "Clancy", ",", "of", "the", "North-West", "Mounted", "Police", ",", "is"]
(1,3) [1,4]		(Clancy) ["Sergeant", "Tom", "Clancy", ","]
```

```
(1,17) [17,33]		(Steve)  ["Steve", ",", "who", "has", "been", "framed", "for", "murder", "by", "``", "Black", "''", "McDougal", "and", "Pierre", "LaRue", "."]
(1,17) [17, 18]		(Steve)  ["Steve", ","]
```

## Learning Latent Personas preprocessing output

For each entity, extract a bag of words $(r, w)$ where $w$ is word lemma, and $r \in \{\text{agent verb},\ \text{patient verb},\ \text{attribute} \}$.

Dependency `type` according to the original paper:

- **agent verb:** _nsubj_, _agent_
- **patient verb:** _dobj_, _nsubjpass_, _iobj_, and any prepositional argument \_prep\_\_
- **attribute:**
  - as `governor`: _nsubj_, _appos_
  - as `dependent`: _nsubj_, _appos_, _amod_, _nn_
- ignore all others

```
{
	"/m/0bxrx5f" : [
		("attribute", "sergeant"),
		("attribute", "Tom"),
		("patient verb", "assigned"),
		("patient verb", "police")
	],
	"/m/0bxrx55" : [],
	"/m/0bxrx7z" : [
		("attribute", "black"),
		("agent verb", "framed")
	],
	"/m/0bxrx6w" : [
		("attribute", "Pierre"),
		("agent verb", "framed")
	]
}
```

We may want to consider including others e.g. `tmod`, `rcmod`. In the example above, the bag of "Steve" is empty, we would miss "Steve framed" and "arrest Steve" due to this rule.

Note also the mistaken interpretation of "Black" as a color.

#### Notes

- "Clancy" could refer to three different characters
- Only useful coreference is "Clancy --> his". If `his` was involved in a dependency that would be classified as one of $\{\text{agent verb},\ \text{patient verb},\ \text{attribute} \}$, then we could add it to Clancy's bag. In this case, "1,poss,brother,16,his,15" is ignored.

## Plan 1

**For each movie:**

1. **Identify Character Name Parts**

   - For each character in `character.metadata_{movie_id}.tsv`, create all possible ordered name part tuples (e.g., `("Sergeant", "Tom", "Clancy")`, `("Tom", "Clancy")`, `("Sergeant", "Tom")`, `("Sergeant", "Clancy")`, `("Sergeant",)`, `("Tom",)`).
   - Preserve the original order of the name parts to limit the search space (arrangements like `("Clancy", "Tom")` are probably very uncommon).
   - Store these tuples in a dictionary with the character’s unique Freebase ID as the value.

2. **Match Name Parts in Tokens**

   - Use a sliding window of length `max(len(name_tuple))` to search `tokens_{movie_id}.csv` for each name tuple from step 1, scanning sentence IDs and token ranges.
   - When a match is found, save the `sentence_id` and token range (`(start, end)` of the match)
   - Decrease window size by 1 and search again, skipping over matched token ranges to prevent duplicate entries
   - Repeat until window size is 0 (or `min(len(name_tuple)) -1`)

3. **Map Characters to Coreference Mentions**

   - For each coreference in `coreferences_{movie_id}.csv`, check if the `head` token ID is within a found character name token range (from step 2.) for the same `sentence_id`.
   - Save the head token ID of this mention as the main identifier (`H`) for that character in the movie.
     - If a character has multiple mentions by name, and hence multiple token ranges in same or different sentences, verify that they form a coreference chain and choose the `head` token ID of the `representative` as the main identifier
     - e.g. ("Sergeant", "Tom", "Clancy") corresponds to the token range [1,3]. This includes the representative `head` token (1,3), i.e. "Clancy".

4. **Collect Coreference Chain Tokens**

   - Create a dictionary `M` where each character (identified by Freebase ID) maps to a set of tokens.
   - Add the head token `H` (from step 3) to `M`, then include any other head tokens in any of the coreference chains linked to `H`.
     - the example has two coreference chains starting at (1,3), one has the same token (1,3) and the other is (1,15) corresponding to the word "his"
   - Using a `set` ensures each head token is added only once per character.

5. **Build Character Bags of Words**
   - Initialize an empty bag of words for each character in `M`.
   - Use the head tokens in `M` to look up dependencies in `dependencies_{movie_id}.csv`.
   - **Filter and Label Dependencies**:
     - Only keep dependency types that could qualify as `attribute`, `agent verb`, or `patient verb`.
   - For each valid dependency:
     - Check if `governor_idx` or `dependent_idx` is a `head` token of some character.
     - Determine its label (`attribute`, `agent verb`, `patient verb`) based on separate lookup tables for `governor` and `dependent` roles.
     - Retrieve the lemma of the other token in the dependency pair from `tokens_{movie_id}.csv`.
     - Append `(dependency_type, lemma)` to the character's bag of words.

#### Notes

- The method in step 1 could result in a misidentification in the rare case that another character, or an unnamed character is also a "Sergeant".
- We may want to filter out characters with small bags of words.
- The bags of words can then be used to build the latent personas we need to generate the character archetypes for the mortality index.
- The same bags of words can be searched through to find if a character dies in the movie (`agent_verb` indicating death of self, or `patient_verb` indicating being killed).

`build_char_word_bags.py` was developed based on the plan here, but the final version may differ in some ways.
