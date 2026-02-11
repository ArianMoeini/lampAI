# LAMP Dataset Expansion Plan

## Target: 7,500 Total Examples (5,000 New + 2,500 Existing)

### Why 7,500?

Research on fine-tuning 3-4B models for structured output tasks shows:
- **2,500 examples** (current): In the sweet spot, achieves 100% on our 21-question benchmark
- **5,000-7,500 examples**: Literature shows 15-20% improvement in generalization on unseen inputs
- **Beyond 10,000**: Diminishing returns for narrow domain tasks (<5% additional gain)
- **Key insight**: Quality and diversity matter more than raw count. AlpaGasus showed 9K filtered > 52K unfiltered

The goal is NOT to improve benchmark scores (already 100%). It's to:
1. **Fix the heart bias** — diverse render examples so the model doesn't default to hearts
2. **Add contextual awareness** — time-of-day, seasons, activities, emotions
3. **Handle real human speech patterns** — conversational, vague, multi-intent requests
4. **Improve generalization** — novel requests the model has never seen

---

## Current Dataset Analysis

### Distribution (2,500 total)
| Category   | Count | %    | Assessment                              |
|------------|-------|------|-----------------------------------------|
| render     | 600   | 24%  | Good count, but **low shape diversity** |
| pattern    | 500   | 20%  | Adequate, mostly template-based         |
| multi_step | 500   | 20%  | Timer-heavy (218/500 are timers)        |
| creative   | 300   | 12%  | Missing key moods and situations        |
| text       | 200   | 8%   | Adequate                                |
| edge_case  | 200   | 8%   | Missing real conversational patterns    |
| mixed      | 200   | 8%   | Good concept, needs expansion           |

### Critical Gaps Identified

**1. Render Heart Bias**
- The system prompt has only ONE pixel-art shape example (heart at line 56-57 of `llm/prompts.py`)
- Current 600 render prompts use ~60 objects from PIXEL_ART_OBJECTS list, but the model overfits to heart-like patterns
- Need: 50+ more unique objects with diverse shapes (geometric, nature, tech, abstract, holiday)

**2. Missing Contextual Awareness**
These appear ZERO times in the current dataset:
- **Moods**: happy, sad, angry, anxious, stressed, relaxed, excited, lonely, tired, bored, inspired
- **Situations**: dinner, sleeping, birthday, christmas, halloween, cold weather
- **Time phrases**: "bedtime", "wake up"
- **Conversational**: "what do you think?", "something for right now", "I'm not sure what I want"

**3. Prompt Style Imbalance**
- 842/2500 (34%) are 3 words or fewer — too many short imperative commands
- Only 87/2500 (3.5%) are casual/conversational — real users are much more conversational
- Average: 5.3 words per prompt — real voice commands tend to be 7-15 words

**4. Multi-Step Overweight on Timers**
- 218/500 (44%) multi_step prompts are timer-related
- Need more: weather simulations, mood transitions, story-telling sequences, routines

---

## New Category Taxonomy (5,000 New Examples)

### Category Distribution for New Data

| Category           | New Count | Total (w/existing) | % of 7,500 | Rationale                                    |
|--------------------|-----------|--------------------|-----------:|----------------------------------------------|
| render_diverse     | 800       | 1,400              | 18.7%      | Fix heart bias with diverse pixel art         |
| contextual         | 800       | 800                | 10.7%      | **NEW**: Time/mood/situation-aware requests   |
| pattern            | 500       | 1,000              | 13.3%      | More pattern combinations                     |
| multi_step         | 500       | 1,000              | 13.3%      | Non-timer sequences                           |
| conversational     | 600       | 600                | 8.0%       | **NEW**: How real humans talk to a lamp       |
| creative           | 500       | 800                | 10.7%      | Expanded mood/vibe vocabulary                 |
| text               | 300       | 500                | 6.7%       | More text + display combos                    |
| mixed              | 400       | 600                | 8.0%       | Render+pattern combos                         |
| edge_case          | 300       | 500                | 6.7%       | Typos, vague, contradictory, multi-language   |
| seasonal_holiday   | 300       | 300                | 4.0%       | **NEW**: Holiday/event-specific requests      |
| **TOTAL**          | **5,000** | **7,500**          | 100%       |                                               |

---

## Detailed Prompt Specifications Per Category

### 1. render_diverse (800 new)

**Goal**: Break the heart bias. Every prompt should produce a DIFFERENT pixel art shape.

**New objects to add (not in current PIXEL_ART_OBJECTS):**

Animals (30): owl, fox, whale, dolphin, penguin, frog, ladybug, octopus, seahorse, turtle, cat (full body), hedgehog, deer, wolf, bat, spider, parrot, hamster, koala, panda, elephant, giraffe, lion, monkey, pig, cow, chicken, unicorn, dragon, phoenix

Nature (20): leaf, tree (pine/oak/palm variants), waterfall, mountain range, volcano, sun with rays, sunset scene, cloud with rain, rainbow arc, wave/ocean, coral, seashell, acorn, pinecone, bamboo, willow tree, cherry blossom, lotus, cactus with flower, mushroom cluster

Food/Drink (20): apple, banana, pizza slice, ice cream cone, cupcake, coffee cup, wine glass, burger, donut, watermelon, cherry, grape bunch, carrot, corn, cookie, lollipop, popsicle, sushi, taco, pretzel

Tech/Modern (15): smartphone, laptop, game controller, headphones, camera, wifi symbol, battery icon, power button, play/pause button, lightbulb (on/off), microphone, satellite, drone, robot (full body), arcade machine

Symbols/Abstract (15): yin-yang, spiral, DNA helix, infinity, hashtag, at-sign, exclamation mark, question mark, checkmark, X mark, plus sign, equal sign, ampersand, asterisk, brackets

Vehicles (10): car, truck, bus, train, helicopter, sailboat, submarine, spaceship, UFO, hot air balloon

Sports (10): basketball, soccer ball, football, tennis racket, baseball bat, golf flag, skateboard, surfboard, dumbbell, medal

Buildings/Places (10): house variants (cottage, mansion, castle), lighthouse, windmill, church, skyscraper, pyramid, bridge, tent, igloo

Faces/Expressions (10): happy face, angry face, surprised face, crying face, cool face (sunglasses), laughing face, sleepy face, thinking face, heart-eyes face, skull and crossbones

Holiday (10): jack-o-lantern, witch hat, santa hat, menorah, dreidel, easter egg, firework, gift with bow, party hat, four-leaf clover

**Prompt templates (mix these):**
```
Direct:        "show a {object}"
With color:    "draw a {color} {object}"
Descriptive:   "pixel art of a {adjective} {object}"
Casual:        "can you make a {object} for me?"
Scene:         "{object} on a {color} background"
Emotional:     "a cheerful {object}" / "a spooky {object}"
Specific:      "small {object} in the center" / "{object} in the top half"
Comparative:   "{object} like the emoji"
```

### 2. contextual (800 new) — **NEW CATEGORY**

**Goal**: Teach the model to be aware of context — time, weather, activity, emotion.

**Sub-categories:**

**Time-aware (200):**
```
"it's 7am, give me something to wake up to"
"late night coding session lighting"
"perfect 3pm afternoon slump picker-upper"
"it's almost bedtime, help me wind down"
"early morning before everyone wakes up"
"lunch break vibes"
"golden hour light for the living room"
"midnight snack lighting"
"6am alarm just went off, ease me into the day"
"it's 10pm and I want to read before sleep"
```

**Activity-aware (200):**
```
"I'm about to start a zoom call"
"hosting a dinner party in an hour"
"kids are coming over for a playdate"
"setting up for a romantic dinner"
"about to do some stretching"
"writing an essay, need focus"
"binge watching a horror series"
"having friends over for board games"
"trying to fall asleep"
"just woke up from a nap"
```

**Mood/Emotion-aware (200):**
```
"I'm feeling really anxious right now"
"just got great news, I'm so happy!"
"feeling kind of down today"
"I'm stressed about a deadline"
"feeling nostalgic, missing home"
"I'm bored, entertain me"
"feeling creative and inspired"
"I need to calm down"
"feeling lonely tonight"
"I'm pumped up, just finished a workout"
```

**Weather/Environment-aware (100):**
```
"it's pouring rain outside"
"beautiful sunny day, complement it"
"there's a thunderstorm, make it cozy inside"
"it's snowing, make it feel warm"
"really hot day, something cool and refreshing"
"foggy and grey outside, brighten things up"
```

**Seasonal-aware (100):**
```
"first day of autumn, set the mood"
"it's the middle of winter and I need warmth"
"spring has arrived, something fresh"
"dog days of summer"
"back to school season"
"end of year reflection mood"
```

### 3. pattern (500 new)

**Expand beyond current templates. New patterns:**

- Multi-color gradients: "gradient from pink through purple to blue"
- Speed descriptions: "something that moves slowly like honey"
- Intensity: "barely visible glow" / "blindingly bright"
- Named patterns: "northern lights pattern" / "lava lamp" / "fireplace flicker"
- Color temperature: "warm white like candlelight" / "cool daylight white"
- Abstract: "something that looks like it's breathing" / "ocean-like movement"
- Synesthesia: "something that sounds like jazz" / "what rain looks like as light"

### 4. multi_step (500 new)

**Reduce timer dominance. Focus on:**

- **Story sequences** (100): "tell a story with light — start dark, build tension, climax, resolve"
- **Nature simulations** (100): "full day cycle from dawn to dusk" / "seasons changing"
- **Routines** (100): "my morning routine: wake up, energize, focus" / "wind-down evening"
- **Games/Interactive** (100): "simon says with colors" / "random color picker"
- **Celebrations** (100): "new year countdown with fireworks" / "birthday candle blowout sequence"

### 5. conversational (600 new) — **NEW CATEGORY**

**Goal**: How real humans actually talk to a smart lamp via voice.

**Sub-categories:**

**Vague/Open-ended (150):**
```
"do something nice"
"I don't know, surprise me"
"something... warm? but not too warm"
"whatever you think looks best"
"just make it look good"
"hmm, I'm not sure what I want"
"something that goes with my mood"
"you pick"
```

**Follow-up style (150):**
(These train the model to handle requests that sound like continuations even though each is standalone)
```
"actually, make it a bit brighter"
"that but in blue instead"
"same thing but slower"
"more of that warm feeling"
"less intense please"
"can you add some sparkle to it"
"keep the color but make it pulse"
"darker version of that"
```

**Questions-as-requests (100):**
```
"what would look good for a date night?"
"what's a good color for focus?"
"can you do something christmassy?"
"is there a sleep mode?"
"what about something for kids?"
"any ideas for a party?"
```

**Multi-intent (100):**
```
"show a star and make the background sparkle"
"I want a timer but make it look pretty"
"something cozy but with a countdown for 10 minutes"
"draw a moon and then transition to a calm blue"
"put up a christmas tree then slowly fade to warm amber"
```

**Verbose/Rambling (100):**
```
"so like, I was thinking, maybe something that's like, you know, kind of like being at the beach at sunset but not too orange, more like a peaceful purple-ish thing"
"okay so I have people coming over in like an hour and I want the lamp to look really nice, something sophisticated but not boring"
"I just came home from work and I'm exhausted, give me something that helps me relax and unwind, nothing too bright"
```

### 6. creative (500 new)

**Expand with missing moods and more abstract concepts:**

- Emotions not in dataset: happy, sad, angry, anxious, stressed, excited, lonely, tired, bored, inspired, grateful, confused, hopeful, proud
- Synesthesia prompts: "what does jazz look like" / "the color of silence" / "make it sound like rain"
- Abstract concepts: "show me possibility" / "what does Monday feel like" / "the color of a fresh start"
- Cultural references: "blade runner vibes" / "studio ghibli aesthetic" / "like a van gogh painting"
- Sensory: "warm like a hug" / "cool like a glass of water" / "soft like a whisper"

### 7. text (300 new)

- Emoji descriptions: "happy face emoji" / "fire emoji" / "thumbs up"
- Dynamic text: "scrolling text HELLO WORLD" / "blinking text SOS"
- Countdowns with display: "countdown from 10 with big numbers"
- Status displays: "show battery at 50%" / "show wifi signal strong"
- Multi-line: "show date Jan 15" / "show temp and weather"

### 8. mixed (400 new)

- Render + ambient: "draw a moon with a calm blue ambient glow"
- Text + pattern: "show PARTY then explode into rainbow"
- Render + timer: "show a candle that slowly melts over 30 minutes"
- Sequence + render: "sunrise → draw a sun → warm gradient"
- Pattern + render overlay: "sparkle background with a star in the center"

### 9. edge_case (300 new)

- **Contradictions** (50): "bright but dark" / "warm ice" / "calm party"
- **Impossible** (50): "show a 3D cube" / "play music" / "change the room temperature"
- **Multilingual** (50): "haz algo bonito" / "montre-moi un coeur" / "zeig mir einen stern"
- **Typos/SMS** (50): "blu lgt pls" / "wrm n cozy" / "prty mode"
- **Very long** (50): 20+ word requests with lots of qualifiers
- **Very short** (50): single words not in current set: "wow", "ugh", "hmm", "nice", "cool", "meh"

### 10. seasonal_holiday (300 new) — **NEW CATEGORY**

- **Christmas** (40): "christmas tree lights" / "cozy christmas eve" / "santa's workshop"
- **Halloween** (40): "haunted house" / "trick or treat mode" / "ghostly glow"
- **Valentine's** (30): "valentine's day" / "love is in the air" / "romantic pink and red"
- **New Year** (30): "new year countdown" / "fireworks at midnight" / "champagne gold"
- **Easter** (20): "easter egg hunt colors" / "spring pastels"
- **4th of July** (20): "patriotic red white blue" / "fireworks show"
- **Diwali** (20): "festival of lights" / "warm golden celebration"
- **Chinese New Year** (20): "lucky red and gold" / "lantern festival"
- **Hanukkah** (20): "menorah lighting" / "blue and silver celebration"
- **General celebrations** (30): "birthday party" / "graduation" / "baby shower"
- **Seasonal** (30): "first snow" / "cherry blossom season" / "harvest moon"

---

## Generation Strategy

### Phase 1: Prompt Generation (Agent Team Task)

Each agent should generate prompts for assigned categories. Rules:
1. Every prompt must be unique — no duplicates within or across categories
2. Exclude all 21 benchmark prompts (listed in `01_generate_prompts.py`)
3. Exclude all 2,500 existing prompts (check against `finetuning/data/prompts.jsonl`)
4. Natural language variation — same request phrased 3-5 different ways
5. Output format: `{"prompt": "...", "category": "..."}`
6. Save to `finetuning/data/prompts_v2.jsonl`

### Phase 2: Response Generation

Use the existing `02_generate_responses.py` script (after fixing the line 84 syntax error):
```bash
python3 02_generate_responses.py --input data/prompts_v2.jsonl --model claude-opus-4-6
```

Estimated API cost: ~5,000 prompts x ~1,800 tokens avg = ~9M tokens
- With Opus: ~$135-180
- With Sonnet: ~$27-45 (recommended for cost savings — quality is sufficient)

### Phase 3: Validation & Merge

1. Run `03_validate_responses.py` on new data
2. Merge with existing train/val split
3. Re-split 90/10 for train/val
4. Target: ~6,750 train + ~750 val

### Phase 4: Training

Same setup as before: Unsloth, bf16, H200
- Adjust epochs: 2 epochs (not 3) since dataset is 3x larger
- Same LR, batch size, optimizer
- Train all 3 models: Llama 3.2 3B, Gemma 3 4B, Phi-4 Mini

---

## Quality Guidelines for Prompt Generation

### DO:
- Write prompts that sound like a real person talking to their lamp
- Include variety in formality: casual ("yo make it blue") to polite ("could you please show me a star?")
- Mix word counts: 1-3 words (30%), 4-8 words (40%), 9+ words (30%)
- Include spelling variations and informal language
- Reference real activities, moods, times, seasons
- Think about what someone would actually say out loud (voice-first interface)

### DON'T:
- Use technical jargon ("execute a gradient render")
- Reference the JSON format or command types
- Include impossible requests (audio, temperature, etc.) — except in edge_case category
- Make prompts that are too similar to each other (dedup aggressively)
- Use the exact benchmark prompts

### Voice-First Considerations:
Since this lamp will use STT (speech-to-text), prompts should sound like natural speech:
- Filler words okay: "um, something warm"
- Trailing off: "maybe like a sunset or..."
- Self-correction: "blue no wait, more like teal"
- Contractions: "don't make it too bright"
- Informal: "lamp, do something cool"

---

## Agent Team Structure

Recommended team of 5 agents, each responsible for:

| Agent | Categories | Count |
|-------|-----------|-------|
| Agent 1 | render_diverse (800) + mixed (400) | 1,200 |
| Agent 2 | contextual (800) | 800 |
| Agent 3 | conversational (600) + edge_case (300) | 900 |
| Agent 4 | pattern (500) + multi_step (500) | 1,000 |
| Agent 5 | creative (500) + text (300) + seasonal_holiday (300) | 1,100 |

Each agent writes to a separate file, then a merge script combines and deduplicates.

---

## Files Reference

- Current prompts: `finetuning/data/prompts.jsonl` (2,500 lines)
- Current training data: `finetuning/data/train.jsonl` (2,268 lines)
- Prompt generator: `finetuning/01_generate_prompts.py`
- Response generator: `finetuning/02_generate_responses.py` (line 84 has syntax error — fix first)
- System prompt: `llm/prompts.py`
- Benchmark: `llm/benchmark_llama.py` (21 reserved prompts)
- Existing benchmark results: `benchmark-results2/results_lamp-gemma-4b.json` (21/21)
