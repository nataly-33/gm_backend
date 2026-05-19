PROMPT_GENERATOR_PROMPT = """
Reformat the following user-provided music description into a simple comma-separated list of audio tags.

User Description: "{user_prompt}"

Follow these guidelines strictly when reformatting. Include a tag from each category below in you final list:
- Include genre (e.g., "rap", "pop", "rock", "electronic")
- Include vocal type (e.g., "male vocal", "female vocal", "spoken word")
- Include instruments actually heard (e.g., "guitar", "piano", "synthesizer", "drums")
- Include mood/energy (e.g., "energetic", "calm", "aggressive", "melancholic")
- Include tempo if known (e.g., "120 bpm", "fast tempo", "slow tempo")
- Include key if known (e.g., "major key", "minor key", "C major")
- The output must be a single line of comma-separated tags. Do not add any other text or explanation. For example: melodic techno, male vocal, electronic, emotional, minor key, 124 bpm, synthesizer, driving, atmospheric

If already a few tags, infer what the user wants and add 2-3 more tags that are synonyms to the users tags with no new categories.

Formatted Tags:
"""

LYRICS_GENERATOR_PROMPT = """
You are an expert songwriter. Generate song lyrics based on the following description.

CRITICAL INSTRUCTION: The requested audio duration is {duration} seconds. 
You MUST scale the length and structure of the lyrics to fit this time perfectly:
- If duration is 30 to 45 seconds: Write strictly 1 [intro], 1 short [verse], and 1 [chorus].
- If duration is 60 to 90 seconds: Write 1 [intro], 2 short [verse]s, and 1 [chorus].
- If duration is 120 to 180 seconds: Write a full song: [intro], [verse 1], [chorus], [verse 2], [chorus], [bridge], and [outro].

Write the lyrics in the EXACT SAME LANGUAGE as the user's description. Keep the rhythm natural.

Example for a short 30-second duration:
"[intro]
(Guitar strum)
Aquí vamos...

[verse]
Caminando por los anillos de la ciudad
Buscando el código en la oscuridad

[chorus]
Porque la vida es una sola, ya lo sé
Brillando fuerte hasta el amanecer"

User Description: "{description}"

Lyrics:
"""
