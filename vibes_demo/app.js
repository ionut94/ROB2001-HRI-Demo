// ===== PandaQuest — Life Sidequests for Students =====

// ---------- Quest Database ----------
const QUESTS = {
    sunny: {
        outdoor: [
            { title: "Sunshine Scholar", desc: "Find a bench outside and read 10 pages of something that isn't a textbook. Let the sun warm your brain.", duration: "20 min", xp: 40, category: "Relaxation", tip: "Bonus points if you discover a new favorite spot on campus." },
            { title: "Sketch the Sky", desc: "Sit somewhere with a view and sketch whatever you see — clouds, buildings, trees. No artistic skills required.", duration: "15 min", xp: 35, category: "Creativity", tip: "Use whatever you have — pen, pencil, even a crayon." },
            { title: "Photowalk Explorer", desc: "Take a 15-minute walk and photograph 5 things that catch your eye. Look for colors, textures, and patterns.", duration: "15 min", xp: 45, category: "Mindfulness", tip: "Try shooting from unusual angles — look up, look down!" },
            { title: "Barefoot Break", desc: "Find some grass, take your shoes off, and stand on it for 5 minutes. Feel the earth. Breathe.", duration: "10 min", xp: 25, category: "Wellness", tip: "This is called 'grounding' and it genuinely reduces stress." },
            { title: "Sun Salutation", desc: "Find a quiet outdoor spot and do 5 rounds of sun salutations (or your best attempt). YouTube a tutorial if needed!", duration: "10 min", xp: 35, category: "Fitness", tip: "Morning sun + stretching = the ultimate energy combo." },
            { title: "Sidewalk Chalk Poet", desc: "Grab some chalk and write an encouraging message or poem on a sidewalk for others to find.", duration: "15 min", xp: 50, category: "Kindness", tip: "Something like 'You're doing great!' can make someone's whole day." },
        ],
        indoor: [
            { title: "Windowsill Garden", desc: "Start a tiny plant project — even a cup with some seeds counts. Name your plant something dramatic.", duration: "15 min", xp: 40, category: "Creativity", tip: "Basil and mint are nearly impossible to kill. Nearly." },
            { title: "Sunny Playlist", desc: "Create a 'golden hour vibes' playlist with at least 8 songs that make you feel warm inside.", duration: "15 min", xp: 30, category: "Relaxation", tip: "Share it with a friend — spread the good vibes." },
        ]
    },
    cloudy: {
        outdoor: [
            { title: "Cloud Cartographer", desc: "Go outside and name 5 cloud shapes you see. The more ridiculous the names, the better.", duration: "10 min", xp: 30, category: "Creativity", tip: "Text a friend your best cloud-shape photo with your name for it." },
            { title: "Wander Without Purpose", desc: "Take a 20-minute walk with zero destination. Turn whenever you feel like it. Get a little lost.", duration: "20 min", xp: 45, category: "Mindfulness", tip: "Leave your phone in your pocket — just walk and observe." },
            { title: "Compliment Quest", desc: "Give 3 genuine compliments to 3 different people during your day. Notice how it makes you both feel.", duration: "All day", xp: 60, category: "Social", tip: "Specific compliments hit different — 'cool jacket' beats 'you look nice'." },
        ],
        indoor: [
            { title: "Cozy Den Builder", desc: "Rearrange your study space or build an epic blanket fort. Make it the coziest spot on earth.", duration: "25 min", xp: 45, category: "Relaxation", tip: "Fairy lights and a warm drink make everything 10x cozier." },
            { title: "Letter to Future You", desc: "Write a letter to yourself 6 months from now. What do you hope for? What are you proud of today?", duration: "15 min", xp: 40, category: "Reflection", tip: "Set a calendar reminder to open it — future you will thank you." },
            { title: "Recipe Roulette", desc: "Pick a random recipe you've never tried and cook/bake it. Doesn't have to be perfect — just fun.", duration: "45 min", xp: 55, category: "Life Skills", tip: "Search 'easy 3-ingredient recipes' if you're feeling cautious." },
        ]
    },
    rainy: {
        outdoor: [
            { title: "Puddle Stomper", desc: "Put on waterproof shoes (or don't) and deliberately stomp through 3 puddles. Embrace the chaos.", duration: "10 min", xp: 30, category: "Joy", tip: "This is scientifically proven to boost your mood. (We made that up. Do it anyway.)" },
            { title: "Rain Listener", desc: "Stand under cover and just listen to the rain for 5 minutes. Count the different sounds you can hear.", duration: "5 min", xp: 25, category: "Mindfulness", tip: "Try to notice: roof rain, ground splashes, gutter trickles, leaf drops." },
        ],
        indoor: [
            { title: "Rainy Day Café", desc: "Make yourself a fancy hot drink — get creative. Cinnamon, honey, whipped cream? Go wild.", duration: "10 min", xp: 25, category: "Self-Care", tip: "Drink it slowly by a window watching the rain. Main character energy." },
            { title: "Memory Lane Mix", desc: "Create a playlist of songs that remind you of happy memories. Write a one-line note about each memory.", duration: "20 min", xp: 40, category: "Reflection", tip: "This becomes an incredible time capsule over the years." },
            { title: "Call Someone You Miss", desc: "Call (not text!) a friend or family member you haven't talked to in a while. Just 10 minutes.", duration: "10 min", xp: 50, category: "Social", tip: "Rainy days + warm phone calls = peak comfort." },
            { title: "Indoor Picnic", desc: "Lay a blanket on your floor, prepare some snacks, and have an indoor picnic. Invite a friend or go solo.", duration: "30 min", xp: 45, category: "Joy", tip: "Put on nature sounds to complete the vibe." },
            { title: "Doodle Storm", desc: "Set a 10-minute timer and fill a whole page with doodles. No erasing allowed. No judgement.", duration: "10 min", xp: 30, category: "Creativity", tip: "Start with a random shape and see where your pen takes you." },
        ]
    },
    snowy: {
        outdoor: [
            { title: "Snow Angel Scholar", desc: "Make a snow angel. Lie there for an extra 30 seconds looking at the sky. Then go finish that assignment.", duration: "10 min", xp: 35, category: "Joy", tip: "Layer up! The quest is fun, hypothermia is not." },
            { title: "Mini Snowperson", desc: "Build the tiniest snowperson you can (must have a face). Put it somewhere unexpected for others to find.", duration: "15 min", xp: 40, category: "Creativity", tip: "Desktop-sized snowpeople are the superior art form." },
            { title: "Fresh Tracks Explorer", desc: "Find fresh, untouched snow and be the first to walk through it. Make a fun pattern with your footprints.", duration: "15 min", xp: 35, category: "Mindfulness", tip: "Spirals, zigzags, or spell out a word — your canvas awaits." },
        ],
        indoor: [
            { title: "Hot Cocoa Connoisseur", desc: "Make hot cocoa from scratch (not a packet!). Experiment with add-ins: marshmallows, cinnamon, chili?", duration: "15 min", xp: 30, category: "Life Skills", tip: "The secret ingredient is always a pinch of salt." },
            { title: "Hygge Hour", desc: "Light a candle (or fake one), grab a blanket, and spend 30 minutes doing something purely for enjoyment.", duration: "30 min", xp: 40, category: "Self-Care", tip: "Hygge (hoo-gah) is the Danish concept of cozy contentment." },
            { title: "Window Watcher", desc: "Sit by a window and watch the snow fall for 10 minutes. No phone. Just snow.", duration: "10 min", xp: 30, category: "Mindfulness", tip: "Notice how no two moments look the same. Like snowflakes!" },
        ]
    },
    stormy: {
        outdoor: [],
        indoor: [
            { title: "Thunder Playlist", desc: "Create the most dramatic, epic playlist you can. Movie soundtracks, orchestral pieces — feel the storm.", duration: "15 min", xp: 35, category: "Creativity", tip: "Play it during the actual thunder for maximum drama." },
            { title: "Power Outage Prep Party", desc: "Gather candles, snacks, and a card game. If the power goes out, you'll be the hero. If not, play cards anyway.", duration: "15 min", xp: 40, category: "Life Skills", tip: "Uno destroys friendships. Choose wisely." },
            { title: "Deep Clean One Thing", desc: "Pick ONE small area (a drawer, your desk, your bag) and organize it beautifully. Before/after photos mandatory.", duration: "20 min", xp: 45, category: "Productivity", tip: "A tidy space = a tidy mind. Science probably agrees." },
            { title: "Storytime", desc: "Write a short story (at least one paragraph) inspired by the sounds of the storm outside.", duration: "20 min", xp: 45, category: "Creativity", tip: "Start with: 'The thunder said something nobody expected...'" },
            { title: "Gratitude Downpour", desc: "Write down 10 things you're genuinely grateful for right now. Be specific — not just 'friends' but which friend and why.", duration: "10 min", xp: 40, category: "Wellness", tip: "Studies show gratitude journaling boosts mood for up to a week." },
        ]
    },
    hot: {
        outdoor: [
            { title: "Hydration Station", desc: "Fill up your water bottle and find the shadiest spot on campus. Sit, sip, and people-watch for 10 minutes.", duration: "10 min", xp: 25, category: "Self-Care", tip: "Add ice cubes or frozen fruit for a glow-up." },
        ],
        indoor: [
            { title: "Frozen Treat Alchemist", desc: "Make a DIY frozen treat — freeze juice, blend a smoothie bowl, or make nice cream from frozen bananas.", duration: "15 min", xp: 35, category: "Life Skills", tip: "Frozen banana + cocoa powder = healthy ice cream. You're welcome." },
            { title: "Cool Down Dance", desc: "Blast some music and have a 5-minute solo dance party in the AC. No choreography required.", duration: "5 min", xp: 25, category: "Joy", tip: "Lock the door first if you need to. No judgement." },
        ]
    },
    cold: {
        outdoor: [
            { title: "Brisk Walk Bingo", desc: "Take a brisk 10-minute walk. Find: something red, something that makes a sound, something beautiful, something tiny.", duration: "10 min", xp: 35, category: "Mindfulness", tip: "Walk fast enough to warm up but slow enough to notice things." },
        ],
        indoor: [
            { title: "Warm Hug in a Mug", desc: "Make the fanciest warm drink you can with what you have. Take 10 minutes to drink it slowly.", duration: "10 min", xp: 25, category: "Self-Care", tip: "Hold the mug with both hands. Feel the warmth. Be present." },
            { title: "Stretch & Restore", desc: "Do a 15-minute gentle stretching routine. Focus on your neck, shoulders, and back — student problem zones.", duration: "15 min", xp: 35, category: "Fitness", tip: "YouTube 'gentle morning stretch' — your future self will thank you." },
        ]
    }
};

const WEATHER_EMOJIS = {
    'Clear': '\u2600\ufe0f',
    'Clouds': '\u2601\ufe0f',
    'Rain': '\ud83c\udf27\ufe0f',
    'Drizzle': '\ud83c\udf26\ufe0f',
    'Thunderstorm': '\u26c8\ufe0f',
    'Snow': '\u2744\ufe0f',
    'Mist': '\ud83c\udf2b\ufe0f',
    'Fog': '\ud83c\udf2b\ufe0f',
    'Haze': '\ud83c\udf2b\ufe0f',
    'Smoke': '\ud83c\udf2b\ufe0f',
    'Dust': '\ud83c\udf2c\ufe0f',
    'Tornado': '\ud83c\udf2a\ufe0f',
};

const MASCOT_MESSAGES = {
    sunny: ["Perfect day to touch some grass! \u2600\ufe0f", "The sun is out and so should you be!", "Vitamin D quest activated!"],
    cloudy: ["Cloudy days are cozy quest days!", "The clouds are giving main character vibes today.", "Perfect lighting for an adventure!"],
    rainy: ["Rain = the world's best study soundtrack!", "Cozy quests incoming! \ud83c\udf27\ufe0f", "The rain can't stop your quest energy!"],
    snowy: ["Snow day side quests hit different! \u2744\ufe0f", "Winter wonderland mode: activated!", "Time for some frosty adventures!"],
    stormy: ["Stay safe inside — indoor quests are just as epic!", "Thunder vibes call for cozy quests!", "Storm outside, warm quests inside!"],
    hot: ["Stay cool, quest warrior! \ud83e\udda7", "Hydrate and conquer!", "Hot day = chill quest energy."],
    cold: ["Bundle up, brave adventurer!", "Cold outside but your quest spirit is warm!", "Cozy quest season is here!"],
};

const CELEBRATION_MSGS = [
    "You're doing amazing! Keep it up!",
    "Your panda guide is SO proud of you!",
    "That's the student-life balance we love to see!",
    "Quest complete! You're basically a legend now.",
    "Your well-being XP is through the roof!",
    "Main character behavior, honestly.",
    "Future you is sending a thank-you note right now.",
    "Procrastination? Don't know her.",
];

// ---------- State ----------
let state = {
    weather: null,
    weatherCategory: 'cloudy',
    currentQuest: null,
    activeQuest: null,
    timerInterval: null,
    timerSeconds: 0,
    xp: parseInt(localStorage.getItem('pandaquest_xp') || '0'),
    streak: parseInt(localStorage.getItem('pandaquest_streak') || '0'),
    lastQuestDate: localStorage.getItem('pandaquest_lastDate') || '',
    history: JSON.parse(localStorage.getItem('pandaquest_history') || '[]'),
};

// ---------- DOM Elements ----------
const $ = (id) => document.getElementById(id);

// ---------- Init ----------
document.addEventListener('DOMContentLoaded', () => {
    createParticles();
    updateStats();
    checkStreak();
    bindEvents();
    getWeatherAndQuest();
});

// ---------- Particles ----------
function createParticles() {
    const container = $('particles');
    for (let i = 0; i < 20; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        const size = Math.random() * 6 + 3;
        p.style.width = size + 'px';
        p.style.height = size + 'px';
        p.style.left = Math.random() * 100 + '%';
        p.style.animationDelay = Math.random() * 8 + 's';
        p.style.animationDuration = (Math.random() * 6 + 6) + 's';
        container.appendChild(p);
    }
}

// ---------- Events ----------
function bindEvents() {
    $('acceptQuest').addEventListener('click', acceptQuest);
    $('rerollQuest').addEventListener('click', rerollQuest);
    $('completeQuest').addEventListener('click', completeQuest);
    $('abandonQuest').addEventListener('click', abandonQuest);
    $('nextQuest').addEventListener('click', nextQuest);
    $('historyToggle').addEventListener('click', toggleHistory);
    $('mascotSvg').addEventListener('click', () => {
        const msgs = MASCOT_MESSAGES[state.weatherCategory] || MASCOT_MESSAGES.cloudy;
        setSpeech(msgs[Math.floor(Math.random() * msgs.length)]);
    });
}

// ---------- Weather ----------
async function getWeatherAndQuest() {
    setSpeech("Let me check the weather for you...");

    try {
        // Get location
        const position = await new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation not supported'));
                return;
            }
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: false,
                timeout: 10000,
                maximumAge: 300000,
            });
        });

        const { latitude, longitude } = position.coords;

        // Fetch weather from Open-Meteo (free, no API key needed)
        const weatherRes = await fetch(
            `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,weather_code,wind_speed_10m&temperature_unit=fahrenheit`
        );
        const weatherData = await weatherRes.json();

        // Reverse geocode for location name
        const geoRes = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json&zoom=10`
        );
        const geoData = await geoRes.json();

        const temp = Math.round(weatherData.current.temperature_2m);
        const code = weatherData.current.weather_code;
        const locationName = geoData.address ?
            `${geoData.address.city || geoData.address.town || geoData.address.village || geoData.address.county || ''}, ${geoData.address.state || geoData.address.country || ''}` :
            'Your Location';

        // Map WMO weather codes to categories
        const weatherInfo = mapWeatherCode(code, temp);

        state.weather = { temp, code, locationName, ...weatherInfo };
        state.weatherCategory = weatherInfo.category;

        // Update UI
        $('weatherIcon').textContent = weatherInfo.emoji;
        $('weatherTemp').textContent = temp + '°F';
        $('weatherDesc').textContent = weatherInfo.description;
        $('weatherLocation').textContent = locationName;
        $('weatherSection').style.display = 'block';

        // Update mascot
        updateMascotAccessory(weatherInfo.category);
        const msgs = MASCOT_MESSAGES[weatherInfo.category] || MASCOT_MESSAGES.cloudy;
        setSpeech(msgs[Math.floor(Math.random() * msgs.length)]);

        // Generate quest
        generateQuest();

    } catch (err) {
        console.error('Weather error:', err);
        setSpeech("I can't find your location — but here's a quest anyway!");
        state.weatherCategory = 'cloudy';
        generateQuest();
    }
}

function mapWeatherCode(code, temp) {
    // WMO Weather interpretation codes
    if (code === 0 || code === 1) {
        if (temp > 90) return { category: 'hot', description: 'Clear & Hot', emoji: '\ud83e\udd75' };
        if (temp < 32) return { category: 'cold', description: 'Clear & Cold', emoji: '\ud83e\udd76' };
        return { category: 'sunny', description: 'Clear Sky', emoji: '\u2600\ufe0f' };
    }
    if (code === 2 || code === 3) return { category: 'cloudy', description: 'Cloudy', emoji: '\u2601\ufe0f' };
    if (code >= 45 && code <= 48) return { category: 'cloudy', description: 'Foggy', emoji: '\ud83c\udf2b\ufe0f' };
    if (code >= 51 && code <= 57) return { category: 'rainy', description: 'Drizzle', emoji: '\ud83c\udf26\ufe0f' };
    if (code >= 61 && code <= 67) return { category: 'rainy', description: 'Rainy', emoji: '\ud83c\udf27\ufe0f' };
    if (code >= 71 && code <= 77) return { category: 'snowy', description: 'Snowy', emoji: '\u2744\ufe0f' };
    if (code >= 80 && code <= 82) return { category: 'rainy', description: 'Rain Showers', emoji: '\ud83c\udf27\ufe0f' };
    if (code >= 85 && code <= 86) return { category: 'snowy', description: 'Snow Showers', emoji: '\ud83c\udf28\ufe0f' };
    if (code >= 95 && code <= 99) return { category: 'stormy', description: 'Thunderstorm', emoji: '\u26c8\ufe0f' };

    // Temperature fallback
    if (temp > 90) return { category: 'hot', description: 'Hot', emoji: '\ud83e\udd75' };
    if (temp < 32) return { category: 'cold', description: 'Cold', emoji: '\ud83e\udd76' };
    return { category: 'cloudy', description: 'Partly Cloudy', emoji: '\u26c5' };
}

// ---------- Mascot Accessories ----------
function updateMascotAccessory(category) {
    const accessory = $('weatherAccessory');
    switch (category) {
        case 'rainy':
            accessory.innerHTML = `
                <line x1="100" y1="20" x2="150" y2="70" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/>
                <path d="M 85 20 Q 100 0 115 20 Q 130 0 140 20 Q 120 35 100 20 Z" fill="#a78bfa" opacity="0.8"/>
            `;
            break;
        case 'snowy':
            accessory.innerHTML = `
                <ellipse cx="150" cy="80" rx="55" ry="10" fill="#c084fc" opacity="0.5"/>
                <rect x="120" y="70" width="60" height="15" rx="2" fill="#7c3aed"/>
                <path d="M 110 85 L 190 85 L 180 70 L 120 70 Z" fill="#7c3aed"/>
            `;
            break;
        case 'sunny':
        case 'hot':
            accessory.innerHTML = `
                <ellipse cx="150" cy="82" rx="60" ry="8" fill="#fbbf24" opacity="0.3"/>
                <rect x="115" y="72" width="70" height="12" rx="2" fill="#fbbf24"/>
                <path d="M 100 84 L 200 84 L 190 72 L 110 72 Z" fill="#f59e0b"/>
                <rect x="125" y="60" width="50" height="15" rx="6" fill="#fbbf24"/>
            `;
            break;
        default:
            accessory.innerHTML = '';
    }
}

// ---------- Quest Generation ----------
function generateQuest() {
    const pool = QUESTS[state.weatherCategory] || QUESTS.cloudy;
    const allQuests = [...(pool.outdoor || []), ...(pool.indoor || [])];

    if (allQuests.length === 0) {
        const fallback = QUESTS.cloudy;
        allQuests.push(...fallback.outdoor, ...fallback.indoor);
    }

    // Pick random quest (avoid repeating last one)
    let quest;
    do {
        quest = allQuests[Math.floor(Math.random() * allQuests.length)];
    } while (quest === state.currentQuest && allQuests.length > 1);

    state.currentQuest = quest;

    // Determine if outdoor/indoor
    const isOutdoor = (pool.outdoor || []).includes(quest);

    // Difficulty stars based on XP
    const stars = quest.xp <= 30 ? '\u2b50' : quest.xp <= 45 ? '\u2b50\u2b50' : '\u2b50\u2b50\u2b50';

    // Update UI
    $('questTypeBadge').textContent = isOutdoor ? 'Outdoor' : 'Indoor';
    $('questDifficulty').innerHTML = stars;
    $('questTitle').textContent = quest.title;
    $('questDescription').textContent = quest.desc;
    $('questDuration').textContent = quest.duration;
    $('questXP').textContent = '+' + quest.xp + ' XP';
    $('questCategory').textContent = quest.category;
    $('questTipText').textContent = quest.tip;

    $('questSection').style.display = 'block';
    $('questCard').classList.remove('shake');
    void $('questCard').offsetWidth; // reflow
    $('questCard').style.animation = 'none';
    void $('questCard').offsetWidth;
    $('questCard').style.animation = '';
}

// ---------- Quest Actions ----------
function acceptQuest() {
    state.activeQuest = { ...state.currentQuest };
    state.timerSeconds = 0;

    $('activeQuestTitle').textContent = state.activeQuest.title;
    $('activeQuestDesc').textContent = state.activeQuest.desc;

    $('questSection').style.display = 'none';
    $('activeQuestSection').style.display = 'block';

    setSpeech("You got this! I believe in you! \ud83d\udc9c");

    // Start timer
    const durationMin = parseInt(state.activeQuest.duration) || 15;
    const totalSeconds = durationMin * 60;

    state.timerInterval = setInterval(() => {
        state.timerSeconds++;
        const mins = Math.floor(state.timerSeconds / 60).toString().padStart(2, '0');
        const secs = (state.timerSeconds % 60).toString().padStart(2, '0');
        $('questTimer').textContent = `${mins}:${secs}`;

        const progress = Math.min((state.timerSeconds / totalSeconds) * 100, 100);
        $('progressFill').style.width = progress + '%';
    }, 1000);
}

function rerollQuest() {
    $('questCard').classList.add('shake');
    setTimeout(() => {
        generateQuest();
        setSpeech("How about this one instead? \ud83c\udfb2");
    }, 300);
}

function completeQuest() {
    clearInterval(state.timerInterval);

    const quest = state.activeQuest;
    const xpEarned = quest.xp;

    // Update state
    state.xp += xpEarned;
    const today = new Date().toISOString().split('T')[0];

    if (state.lastQuestDate !== today) {
        if (isConsecutiveDay(state.lastQuestDate, today)) {
            state.streak++;
        } else {
            state.streak = 1;
        }
        state.lastQuestDate = today;
    }

    // Add to history
    state.history.unshift({
        title: quest.title,
        xp: xpEarned,
        date: today,
        category: quest.category,
    });
    if (state.history.length > 50) state.history.pop();

    // Save
    saveState();
    updateStats();

    // Show celebration
    $('activeQuestSection').style.display = 'none';
    $('xpEarned').textContent = '+' + xpEarned + ' XP';
    $('celebrationMsg').textContent = CELEBRATION_MSGS[Math.floor(Math.random() * CELEBRATION_MSGS.length)];
    $('celebrationSection').style.display = 'block';

    setSpeech("AMAZING! You did it!! \ud83c\udf89\ud83d\udc3c");

    // Confetti
    spawnConfetti();

    // Update history display
    renderHistory();
}

function abandonQuest() {
    clearInterval(state.timerInterval);
    $('activeQuestSection').style.display = 'none';
    $('questSection').style.display = 'block';
    setSpeech("No worries! There's always another quest waiting. \ud83d\udc9c");
}

function nextQuest() {
    $('celebrationSection').style.display = 'none';
    generateQuest();
    setSpeech("Ready for another adventure? \ud83d\ude80");
}

// ---------- Streak Logic ----------
function checkStreak() {
    const today = new Date().toISOString().split('T')[0];
    if (state.lastQuestDate && !isConsecutiveDay(state.lastQuestDate, today) && state.lastQuestDate !== today) {
        // Streak broken if more than 1 day gap
        const lastDate = new Date(state.lastQuestDate);
        const todayDate = new Date(today);
        const diffDays = Math.floor((todayDate - lastDate) / (1000 * 60 * 60 * 24));
        if (diffDays > 1) {
            state.streak = 0;
            saveState();
        }
    }
}

function isConsecutiveDay(dateStr1, dateStr2) {
    if (!dateStr1) return false;
    const d1 = new Date(dateStr1);
    const d2 = new Date(dateStr2);
    const diff = Math.floor((d2 - d1) / (1000 * 60 * 60 * 24));
    return diff === 1;
}

// ---------- State Management ----------
function saveState() {
    localStorage.setItem('pandaquest_xp', state.xp.toString());
    localStorage.setItem('pandaquest_streak', state.streak.toString());
    localStorage.setItem('pandaquest_lastDate', state.lastQuestDate);
    localStorage.setItem('pandaquest_history', JSON.stringify(state.history));
}

function updateStats() {
    $('xpCount').textContent = state.xp;
    $('streakCount').textContent = state.streak;
}

// ---------- Speech Bubble ----------
function setSpeech(text) {
    const bubble = $('speechBubble');
    bubble.style.animation = 'none';
    void bubble.offsetWidth;
    bubble.style.animation = '';
    $('speechText').textContent = text;
}

// ---------- History ----------
function toggleHistory() {
    const list = $('historyList');
    const arrow = document.querySelector('.toggle-arrow');
    if (list.style.display === 'none') {
        renderHistory();
        list.style.display = 'flex';
        arrow.classList.add('open');
    } else {
        list.style.display = 'none';
        arrow.classList.remove('open');
    }
}

function renderHistory() {
    const list = $('historyList');
    if (state.history.length === 0) {
        list.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem; padding: 10px 0;">No quests completed yet. Your adventure begins now!</p>';
        return;
    }

    list.innerHTML = state.history.slice(0, 20).map(item => `
        <div class="history-item">
            <div class="history-item-info">
                <div class="history-item-title">${escapeHtml(item.title)}</div>
                <div class="history-item-date">${formatDate(item.date)} · ${escapeHtml(item.category)}</div>
            </div>
            <div class="history-item-xp">+${item.xp} XP</div>
        </div>
    `).join('');
}

function formatDate(dateStr) {
    const d = new Date(dateStr + 'T12:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ---------- Confetti ----------
function spawnConfetti() {
    const container = $('confetti');
    container.innerHTML = '';
    const colors = ['#a855f7', '#f0abfc', '#fbbf24', '#34d399', '#60a5fa', '#f472b6', '#c084fc'];
    for (let i = 0; i < 40; i++) {
        const piece = document.createElement('div');
        piece.className = 'confetti-piece';
        piece.style.left = Math.random() * 100 + '%';
        piece.style.background = colors[Math.floor(Math.random() * colors.length)];
        piece.style.animationDelay = Math.random() * 0.5 + 's';
        piece.style.animationDuration = (Math.random() * 1 + 1) + 's';
        const size = Math.random() * 8 + 5;
        piece.style.width = size + 'px';
        piece.style.height = size + 'px';
        piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
        container.appendChild(piece);
    }
}
