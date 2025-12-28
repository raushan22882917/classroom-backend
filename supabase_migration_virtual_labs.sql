-- Virtual Labs Database Migration
-- This creates all the necessary tables for the Virtual Labs feature

-- Drop existing tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS virtual_lab_ai_assistance CASCADE;
DROP TABLE IF EXISTS virtual_lab_interactions CASCADE;
DROP TABLE IF EXISTS virtual_lab_sessions CASCADE;
DROP TABLE IF EXISTS virtual_labs CASCADE;

-- Drop existing functions if they exist
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Create virtual_labs table
CREATE TABLE IF NOT EXISTS virtual_labs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    subject VARCHAR(50) NOT NULL CHECK (subject IN ('mathematics', 'physics', 'chemistry', 'biology')),
    class_grade INTEGER NOT NULL CHECK (class_grade >= 1 AND class_grade <= 12),
    topic VARCHAR(100) NOT NULL,
    html_content TEXT NOT NULL,
    css_content TEXT DEFAULT '',
    js_content TEXT DEFAULT '',
    thumbnail_url TEXT,
    difficulty_level VARCHAR(20) NOT NULL CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    estimated_duration INTEGER NOT NULL CHECK (estimated_duration >= 5 AND estimated_duration <= 300),
    learning_objectives JSONB NOT NULL DEFAULT '[]'::jsonb,
    prerequisites JSONB DEFAULT '[]'::jsonb,
    tags JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create virtual_lab_sessions table
CREATE TABLE IF NOT EXISTS virtual_lab_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    lab_id UUID NOT NULL REFERENCES virtual_labs(id) ON DELETE CASCADE,
    session_name VARCHAR(200),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_minutes INTEGER CHECK (duration_minutes >= 0),
    completion_status VARCHAR(20) NOT NULL DEFAULT 'in_progress' 
        CHECK (completion_status IN ('not_started', 'in_progress', 'completed', 'abandoned')),
    performance_score DECIMAL(5,2) CHECK (performance_score >= 0 AND performance_score <= 100),
    feedback TEXT,
    interactions_count INTEGER DEFAULT 0,
    gesture_commands_used INTEGER DEFAULT 0,
    ai_assistance_requests INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create virtual_lab_interactions table
CREATE TABLE IF NOT EXISTS virtual_lab_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES virtual_lab_sessions(id) ON DELETE CASCADE,
    interaction_type VARCHAR(20) NOT NULL 
        CHECK (interaction_type IN ('click', 'drag', 'gesture', 'input', 'selection', 'measurement', 'calculation')),
    interaction_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    element_id VARCHAR(100),
    gesture_type VARCHAR(50),
    performance_impact DECIMAL(3,2) CHECK (performance_impact >= -1 AND performance_impact <= 1),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create virtual_lab_ai_assistance table
CREATE TABLE IF NOT EXISTS virtual_lab_ai_assistance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES virtual_lab_sessions(id) ON DELETE CASCADE,
    user_query TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    context_data JSONB DEFAULT '{}'::jsonb,
    response_type VARCHAR(20) NOT NULL DEFAULT 'explanation'
        CHECK (response_type IN ('explanation', 'hint', 'correction', 'encouragement', 'guidance')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_virtual_labs_subject_grade ON virtual_labs(subject, class_grade);
CREATE INDEX IF NOT EXISTS idx_virtual_labs_active ON virtual_labs(is_active);
CREATE INDEX IF NOT EXISTS idx_virtual_labs_created_by ON virtual_labs(created_by);
CREATE INDEX IF NOT EXISTS idx_virtual_labs_created_at ON virtual_labs(created_at);

CREATE INDEX IF NOT EXISTS idx_virtual_lab_sessions_user_id ON virtual_lab_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_virtual_lab_sessions_lab_id ON virtual_lab_sessions(lab_id);
CREATE INDEX IF NOT EXISTS idx_virtual_lab_sessions_status ON virtual_lab_sessions(completion_status);
CREATE INDEX IF NOT EXISTS idx_virtual_lab_sessions_created_at ON virtual_lab_sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_virtual_lab_interactions_session_id ON virtual_lab_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_virtual_lab_interactions_timestamp ON virtual_lab_interactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_virtual_lab_interactions_type ON virtual_lab_interactions(interaction_type);

CREATE INDEX IF NOT EXISTS idx_virtual_lab_ai_assistance_session_id ON virtual_lab_ai_assistance(session_id);
CREATE INDEX IF NOT EXISTS idx_virtual_lab_ai_assistance_created_at ON virtual_lab_ai_assistance(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_virtual_labs_updated_at 
    BEFORE UPDATE ON virtual_labs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_virtual_lab_sessions_updated_at 
    BEFORE UPDATE ON virtual_lab_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE virtual_labs ENABLE ROW LEVEL SECURITY;
ALTER TABLE virtual_lab_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE virtual_lab_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE virtual_lab_ai_assistance ENABLE ROW LEVEL SECURITY;

-- RLS Policies for virtual_labs
-- Allow read access to active labs for all authenticated users
CREATE POLICY "Allow read access to active virtual labs" ON virtual_labs
    FOR SELECT USING (is_active = true);

-- Allow creators to manage their own labs
CREATE POLICY "Allow creators to manage their virtual labs" ON virtual_labs
    FOR ALL USING (auth.uid() = created_by);

-- Allow admins/teachers to create labs (you may need to adjust based on your user roles)
CREATE POLICY "Allow authenticated users to create virtual labs" ON virtual_labs
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- RLS Policies for virtual_lab_sessions
-- Users can only access their own sessions
CREATE POLICY "Users can manage their own lab sessions" ON virtual_lab_sessions
    FOR ALL USING (auth.uid() = user_id);

-- RLS Policies for virtual_lab_interactions
-- Users can only access interactions from their own sessions
CREATE POLICY "Users can manage interactions from their sessions" ON virtual_lab_interactions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM virtual_lab_sessions 
            WHERE virtual_lab_sessions.id = virtual_lab_interactions.session_id 
            AND virtual_lab_sessions.user_id = auth.uid()
        )
    );

-- RLS Policies for virtual_lab_ai_assistance
-- Users can only access AI assistance from their own sessions
CREATE POLICY "Users can manage AI assistance from their sessions" ON virtual_lab_ai_assistance
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM virtual_lab_sessions 
            WHERE virtual_lab_sessions.id = virtual_lab_ai_assistance.session_id 
            AND virtual_lab_sessions.user_id = auth.uid()
        )
    );

-- Insert some sample data for testing
INSERT INTO virtual_labs (
    title, 
    description, 
    subject, 
    class_grade, 
    topic, 
    html_content, 
    css_content, 
    js_content, 
    difficulty_level, 
    estimated_duration, 
    learning_objectives, 
    prerequisites, 
    tags,
    created_by
) VALUES (
    'Simple Pendulum Motion',
    'Explore the relationship between pendulum length and period of oscillation through interactive simulation.',
    'physics',
    11,
    'Oscillations and Waves',
    '<!DOCTYPE html>
<html>
<head>
    <title>Simple Pendulum Lab</title>
</head>
<body>
    <div id="lab-container">
        <h1>Simple Pendulum Motion Lab</h1>
        <div id="pendulum-setup">
            <canvas id="pendulum-canvas" width="600" height="400"></canvas>
        </div>
        <div id="controls">
            <label>Length (cm): <input type="range" id="length-slider" min="20" max="200" value="100"></label>
            <label>Amplitude (degrees): <input type="range" id="amplitude-slider" min="5" max="45" value="15"></label>
            <button id="start-btn">Start</button>
            <button id="stop-btn">Stop</button>
            <button id="reset-btn">Reset</button>
        </div>
        <div id="measurements">
            <p>Period: <span id="period-display">0.00</span> seconds</p>
            <p>Frequency: <span id="frequency-display">0.00</span> Hz</p>
        </div>
    </div>
</body>
</html>',
    '#lab-container { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
#pendulum-canvas { border: 1px solid #ccc; background: #f9f9f9; }
#controls { margin: 20px 0; }
#controls label { display: block; margin: 10px 0; }
#controls button { margin: 5px; padding: 10px 20px; }
#measurements { background: #e9e9e9; padding: 15px; border-radius: 5px; }',
    'let pendulum = {
    length: 100,
    amplitude: 15,
    angle: 0,
    angularVelocity: 0,
    isRunning: false,
    startTime: 0,
    period: 0
};

function initializePendulum() {
    const canvas = document.getElementById("pendulum-canvas");
    const ctx = canvas.getContext("2d");
    
    // Animation and physics code here
    console.log("Pendulum lab initialized");
}

document.addEventListener("DOMContentLoaded", initializePendulum);',
    'intermediate',
    45,
    '["Understand the relationship between pendulum length and period", "Calculate period using the pendulum formula", "Analyze the effect of amplitude on period"]',
    '["Basic trigonometry", "Understanding of periodic motion"]',
    '["pendulum", "physics", "oscillations", "period", "frequency"]',
    '00000000-0000-0000-0000-000000000000'  -- Replace with actual user UUID
),
(
    'Acid-Base Titration',
    'Virtual chemistry lab for performing acid-base titrations and understanding neutralization reactions.',
    'chemistry',
    12,
    'Acids and Bases',
    '<!DOCTYPE html>
<html>
<head>
    <title>Acid-Base Titration Lab</title>
</head>
<body>
    <div id="lab-container">
        <h1>Acid-Base Titration Lab</h1>
        <div id="titration-setup">
            <div id="burette">
                <div id="titrant-level"></div>
            </div>
            <div id="flask">
                <div id="solution"></div>
            </div>
        </div>
        <div id="controls">
            <button id="add-titrant">Add Titrant (1 mL)</button>
            <button id="add-indicator">Add Indicator</button>
            <button id="reset-experiment">Reset</button>
        </div>
        <div id="measurements">
            <p>Volume Added: <span id="volume-display">0.0</span> mL</p>
            <p>pH: <span id="ph-display">7.0</span></p>
            <p>Color: <span id="color-display">Clear</span></p>
        </div>
    </div>
</body>
</html>',
    '#lab-container { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
#titration-setup { display: flex; justify-content: center; align-items: flex-end; height: 300px; }
#burette { width: 50px; height: 200px; border: 2px solid #333; position: relative; }
#flask { width: 100px; height: 100px; border: 2px solid #333; border-radius: 0 0 50px 50px; margin-left: 20px; }
#solution { height: 100%; transition: background-color 0.3s; }
#controls { margin: 20px 0; text-align: center; }
#controls button { margin: 5px; padding: 10px 20px; }',
    'let titration = {
    volumeAdded: 0,
    pH: 7.0,
    indicatorAdded: false,
    equivalencePoint: 25.0
};

function updateDisplay() {
    document.getElementById("volume-display").textContent = titration.volumeAdded.toFixed(1);
    document.getElementById("ph-display").textContent = titration.pH.toFixed(1);
    
    // Update solution color based on pH and indicator
    const solution = document.getElementById("solution");
    if (titration.indicatorAdded) {
        if (titration.pH < 7) {
            solution.style.backgroundColor = "#ffcccc"; // Pink (acidic)
        } else {
            solution.style.backgroundColor = "#ccffcc"; // Green (basic)
        }
    }
}

document.addEventListener("DOMContentLoaded", function() {
    console.log("Titration lab initialized");
    updateDisplay();
});',
    'advanced',
    60,
    '["Understand neutralization reactions", "Calculate molarity from titration data", "Identify equivalence point"]',
    '["Molarity calculations", "Acid-base theory", "Chemical equations"]',
    '["chemistry", "titration", "acids", "bases", "neutralization"]',
    '00000000-0000-0000-0000-000000000000'  -- Replace with actual user UUID
);

-- Add comments for documentation
COMMENT ON TABLE virtual_labs IS 'Stores virtual lab definitions with HTML/CSS/JS content';
COMMENT ON TABLE virtual_lab_sessions IS 'Tracks individual user sessions working on virtual labs';
COMMENT ON TABLE virtual_lab_interactions IS 'Logs detailed user interactions within virtual labs';
COMMENT ON TABLE virtual_lab_ai_assistance IS 'Stores AI assistance requests and responses for virtual labs';

COMMENT ON COLUMN virtual_labs.html_content IS 'HTML content for the virtual lab interface';
COMMENT ON COLUMN virtual_labs.css_content IS 'CSS styles for the virtual lab';
COMMENT ON COLUMN virtual_labs.js_content IS 'JavaScript code for lab functionality';
COMMENT ON COLUMN virtual_labs.learning_objectives IS 'JSON array of learning objectives';
COMMENT ON COLUMN virtual_labs.prerequisites IS 'JSON array of prerequisite knowledge';
COMMENT ON COLUMN virtual_labs.tags IS 'JSON array of tags for categorization';

COMMENT ON COLUMN virtual_lab_interactions.interaction_data IS 'JSON object containing interaction details';
COMMENT ON COLUMN virtual_lab_interactions.performance_impact IS 'Score impact of this interaction (-1 to 1)';

COMMENT ON COLUMN virtual_lab_ai_assistance.context_data IS 'JSON object with lab state and context for AI';
COMMENT ON COLUMN virtual_lab_ai_assistance.response_type IS 'Type of AI response provided';