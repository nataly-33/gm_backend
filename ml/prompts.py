PROMPT_GENERATOR_PROMPT = """
Reformat the following user-provided music description into a simple comma-separated list of audio tags.

User Description: "{user_prompt}"

Follow these guidelines strictly when reformatting. Include a tag from each category below in your final list:
- Include genre (e.g., "rap", "pop", "rock", "electronic", "reggaeton", "bachata")
- Include instruments actually heard (e.g., "guitar", "piano", "synthesizer", "drums")
- Include mood/energy (e.g., "energetic", "calm", "aggressive", "melancholic", "romantic")
- Include tempo if known (e.g., "120 bpm", "fast tempo", "slow tempo")
- Include key if known (e.g., "major key", "minor key")
- The output must be a single line of comma-separated tags. Do NOT include vocal type or language tags — those are added separately. Do not add any other text or explanation.
- Example: pop, romantic, piano, guitar, slow tempo, minor key, melancholic, dreamy

If already a few tags, infer what the user wants and add 2-3 more tags that complement the style.

Formatted Tags:
"""

LYRICS_GENERATOR_PROMPT = """
You are an expert songwriter specializing in phonetically natural lyrics for vocal synthesis.

CRITICAL INSTRUCTION: The requested audio duration is {duration} seconds.
You MUST scale the length and structure of the lyrics to fit this time perfectly:
- If duration is 30 to 45 seconds: Write strictly 1 short [verse] and 1 [chorus]. Do NOT include an [intro] section.
- If duration is 60 to 90 seconds: Write 2 short [verse]s and 1 [chorus]. Do NOT include an [intro] section.
- If duration is 120 to 180 seconds: Write a full song: [intro], [verse 1], [chorus], [verse 2], [chorus], [bridge], and [outro].

IMPORTANT: For songs under 90 seconds, do NOT use an [intro] section. Start singing immediately with [verse] or [verse 1]. The vocalist should start within the first 5-8 seconds.

For songs 120 seconds or longer that include an [intro]: the [intro] section must contain a single instrument cue line only (e.g. `(piano intro)`), not sung text. Keep it under 5 seconds. Do not write lyrics inside [intro].

LANGUAGE: Write ALL lyrics EXCLUSIVELY in {language_instruction}. Do NOT mix languages.
- CRITICAL: Even if the song description is written in a different language, your lyrics MUST be written entirely in {language_instruction}. Translate the ideas, not the words.
- If writing in Spanish: prefer words with open vowels (a, e, o), keep lines 6–10 syllables, use everyday spoken Spanish (avoid rare literary words), no hard consonant clusters.
- If writing in English: use natural spoken phrasing, keep lines rhythmically natural.

FORMATTING RULES:
- Use section markers: [verse], [verse 1], [verse 2], [chorus], [bridge], [outro] (and [intro] only for songs over 90 seconds)
- To suggest an instrument at the very start of a short song, add a single inline cue on the first line of [verse], e.g. `(guitar) First line of lyrics here`
- Use (instrument cue) only in [intro] (when present) and [outro], not mid-verse
- Each line should be singable in one breath phrase

User Description: "{description}"

Lyrics:
"""
