IMAGE PROMPT (image_prompt) — the VERY FIRST FRAME, BEFORE any action begins. One STILL PHOTOGRAPH, zero motion.
Show the INITIAL STATE: if clothing will be removed, it's still on. If someone enters, the room is empty.
The video_prompt handles all transitions. The image_prompt shows where the scene STARTS, not where it ends.

FORMAT:
"create new scene, [detailed environment]. [subject/objects in frame] [static pose/position]. [lighting, atmosphere, composition]."

RULES:
- Always start with "create new scene, [detailed environment]."
- Describe the full frame: environment, setting, lighting, atmosphere, and composition.
- Describe any people by VISIBLE appearance only (clothing, hair, position) — never by name.
- Do NOT invent people or characters that the Scene Concept does not include.
- Do NOT invent clothing or wardrobe details beyond the Scene Concept.
- Describe POSES as static states: "standing with arms crossed", "seated at desk", "leaning against railing".
- Describe EXPRESSIONS as states: "stern expression", "wide grin" — NOT "expression changes to".
- NO motion verbs (walking, running, reaching, turning, heaving, dancing, gesturing).
- NO motion-photography effects: no motion blur, speed lines, long exposure, camera
  shake. The still frame is SHARP — motion belongs to the video.
- No character names. Describe a frozen moment — a photograph, not a video frame.

STYLE:
- Match the visual medium and art style named in the Scene Concept.
- If the Scene Concept specifies a stylized medium (hand-drawn, anime, oil painting,
  pixel art, etc.), NAME that medium explicitly; otherwise stay photorealistic/cinematic.
- Keep each prompt self-contained — the image model has no memory of other scenes.

EXAMPLES (format only — never copy their subjects, objects, or settings into your prompts):
- "create new scene, empty throne room in black marble. A single gold crown rests on a dark table in the foreground, floor-to-ceiling glass behind shows a night city skyline. Cold moonlight, long shadows."
- "create new scene, rainy neon alley at night. Wet asphalt reflects pink and blue signage, steam rising from a grate. Cinematic wide shot, shallow depth of field."
