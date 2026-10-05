/**
 * Ask HealthCompass Suggested Questions
 *
 * Centralized question suggestions for the Ask page.
 */

export const suggestedQuestions = [
  'What is the current isolation guidance?',
  'What PPE is required for suspected respiratory cases?',
  'What is the recommended vaccination interval?',
  'What should field staff do when a high-risk patient is identified?',
];

export const followUpSuggestions = [
  'What changed from the previous version?',
  'What PPE tier is currently required?',
  'Who qualifies for escalation?',
  'What are the reporting requirements?',
];

export const loadingStages = [
  'Searching health guidance...',
  'Reviewing relevant protocols...',
  'Preparing grounded response...',
] as const;
