/**
 * Test data for E2E scenarios
 */

export const testIdeas = {
  hunch: {
    message: "I have an idea about using AI to help employees capture their creative hunches before they forget them",
    expectedTitle: "AI",
  },
  withChallenge: {
    message: "The challenge is that employees often have great ideas during meetings but forget them by the time they get back to their desk",
  },
  withApproach: {
    message: "My approach would be to create a simple voice memo feature that transcribes and categorizes ideas automatically",
  },
};

export const testActions = [
  "Research existing voice memo apps",
  "Create prototype of transcription feature",
  "User test with 5 employees",
];

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
