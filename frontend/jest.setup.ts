import '@testing-library/jest-dom';

// Ensure global.fetch exists for tests that spy on it
if (!(global as any).fetch) {
  (global as any).fetch = jest.fn();
}



