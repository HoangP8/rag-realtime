-- Database schema for Medical Chatbot

-- User profiles table
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    first_name TEXT,
    last_name TEXT,
    date_of_birth DATE,
    medical_history_id UUID,
    preferences JSONB DEFAULT '{"isVietnamese": true, "use_rag": true}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User roles table
CREATE TABLE IF NOT EXISTS public.user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    role TEXT NOT NULL CHECK (role IN ('patient', 'provider', 'admin')),
    verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversations table
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    title TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    tags TEXT[] DEFAULT '{}'::TEXT[],
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    message_type TEXT NOT NULL DEFAULT 'text' CHECK (message_type IN ('text', 'voice')),
    voice_url TEXT,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Voice sessions table
CREATE TABLE IF NOT EXISTS public.voice_sessions (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    conversation_id UUID REFERENCES public.conversations(id),
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive', 'error')),
    token TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    config JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversation context table
CREATE TABLE IF NOT EXISTS public.conversation_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    context_data JSONB DEFAULT '{}'::JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON public.user_profiles(id);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON public.user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_user_id ON public.voice_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_conversation_id ON public.voice_sessions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversation_context_conversation_id ON public.conversation_context(conversation_id);

-- Set up Row Level Security (RLS)
-- Enable RLS on all tables
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.voice_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_context ENABLE ROW LEVEL SECURITY;

-- Create policies
-- User profiles: Users can only read and update their own profiles
CREATE POLICY user_profiles_select ON public.user_profiles
    FOR SELECT USING (auth.uid() = id);
    
CREATE POLICY user_profiles_insert ON public.user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);
    
CREATE POLICY user_profiles_update ON public.user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- User roles: Users can only read their own roles
CREATE POLICY user_roles_select ON public.user_roles
    FOR SELECT USING (auth.uid() = user_id);

-- Conversations: Users can only access their own conversations
CREATE POLICY conversations_select ON public.conversations
    FOR SELECT USING (auth.uid() = user_id);
    
CREATE POLICY conversations_insert ON public.conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);
    
CREATE POLICY conversations_update ON public.conversations
    FOR UPDATE USING (auth.uid() = user_id);
    
CREATE POLICY conversations_delete ON public.conversations
    FOR DELETE USING (auth.uid() = user_id);

-- Messages: Users can only access messages in their own conversations
CREATE POLICY messages_select ON public.messages
    FOR SELECT USING (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );
    
CREATE POLICY messages_insert ON public.messages
    FOR INSERT WITH CHECK (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );

-- Voice sessions: Users can only access their own voice sessions
CREATE POLICY voice_sessions_select ON public.voice_sessions
    FOR SELECT USING (auth.uid() = user_id);
    
CREATE POLICY voice_sessions_insert ON public.voice_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);
    
CREATE POLICY voice_sessions_update ON public.voice_sessions
    FOR UPDATE USING (auth.uid() = user_id);
    
CREATE POLICY voice_sessions_delete ON public.voice_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Conversation context: Users can only access context for their own conversations
CREATE POLICY conversation_context_select ON public.conversation_context
    FOR SELECT USING (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );
    
CREATE POLICY conversation_context_insert ON public.conversation_context
    FOR INSERT WITH CHECK (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );
    
CREATE POLICY conversation_context_update ON public.conversation_context
    FOR UPDATE USING (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );

-- Create functions for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updating timestamps
CREATE TRIGGER update_user_profiles_updated_at
BEFORE UPDATE ON public.user_profiles
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_roles_updated_at
BEFORE UPDATE ON public.user_roles
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at
BEFORE UPDATE ON public.conversations
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_voice_sessions_updated_at
BEFORE UPDATE ON public.voice_sessions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
