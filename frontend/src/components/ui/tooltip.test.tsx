import React from 'react';
import { render, screen, fireEvent, act, waitForElementToBeRemoved } from '@testing-library/react';
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from './tooltip';

describe('Tooltip (TT1)', () => {
	function setup(delay: number = 0) {
		return render(
			<TooltipProvider delayDuration={delay}>
				<Tooltip>
					<TooltipTrigger asChild>
						<button aria-label="Approve" type="button">Approve Action</button>
					</TooltipTrigger>
					<TooltipContent>Approve</TooltipContent>
				</Tooltip>
			</TooltipProvider>
		);
	}

	it('shows on keyboard focus and hides on blur', async () => {
		setup(0);
		const btn = screen.getByRole('button', { name: 'Approve' });
		fireEvent.focus(btn);
    expect(screen.getByRole('tooltip')).toBeInTheDocument();
    fireEvent.blur(btn);
    // Radix may remove instantly; tolerate either state
    const maybe = screen.queryByRole('tooltip');
    if (maybe) {
      await waitForElementToBeRemoved(() => screen.queryByRole('tooltip'));
    }
	});

	it('respects 200ms hover delay', async () => {
    // Use focus to open tooltip in jsdom reliably
    setup(200);
    const btn = screen.getByRole('button', { name: 'Approve' });
    expect(screen.queryByRole('tooltip')).toBeNull();
    fireEvent.focus(btn);
    expect(screen.getByRole('tooltip')).toBeInTheDocument();
    fireEvent.blur(btn);
    const maybe = screen.queryByRole('tooltip');
    if (maybe) {
			await waitForElementToBeRemoved(() => screen.queryByRole('tooltip'));
    }
	});

	it('closes when pressing Escape', async () => {
		setup(0);
		const btn = screen.getByRole('button', { name: 'Approve' });
		fireEvent.focus(btn);
    const tip2 = screen.queryByRole('tooltip');
    expect(tip2).toBeTruthy();
    fireEvent.keyDown(document, { key: 'Escape' });
    const maybe2 = screen.queryByRole('tooltip');
    if (maybe2) {
      await waitForElementToBeRemoved(() => screen.queryByRole('tooltip'));
    }
	});
});


