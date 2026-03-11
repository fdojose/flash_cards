-- Spiral Learning Database Migration
-- Add new fields to user_learning_sets table for spiral learning functionality

-- Add spiral learning tracking fields
ALTER TABLE user_learning_sets 
ADD COLUMN IF NOT EXISTS completed_integration_cycles INTEGER DEFAULT 0;

ALTER TABLE user_learning_sets 
ADD COLUMN IF NOT EXISTS spiral_review_mode BOOLEAN DEFAULT FALSE;

ALTER TABLE user_learning_sets 
ADD COLUMN IF NOT EXISTS last_spiral_review TIMESTAMP WITH TIME ZONE;

-- Update any existing records to have default values
UPDATE user_learning_sets 
SET completed_integration_cycles = 0 
WHERE completed_integration_cycles IS NULL;

UPDATE user_learning_sets 
SET spiral_review_mode = FALSE 
WHERE spiral_review_mode IS NULL;

-- Create index on spiral review mode for better query performance
CREATE INDEX IF NOT EXISTS idx_user_learning_sets_spiral_review_mode 
ON user_learning_sets(spiral_review_mode) WHERE spiral_review_mode = TRUE;

-- Create index on completed integration cycles
CREATE INDEX IF NOT EXISTS idx_user_learning_sets_integration_cycles 
ON user_learning_sets(completed_integration_cycles);

-- Verify the changes
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'user_learning_sets' 
AND column_name IN ('completed_integration_cycles', 'spiral_review_mode', 'last_spiral_review');
