/**
 * Saved Items API Client
 * API client for My Stuff dashboard saved items
 */

import { WEBUI_API_BASE_URL } from '$lib/constants';

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

export type SeriesConfig = {
	column: string;  // Original column name from SQL (used for matching)
	name: string;    // Display name (editable by user)
	color: string;
};

export type SavedItem = {
	id: string;
	user_id: string;
	chat_id: string | null;
	message_id: string;
	type: 'line' | 'bar' | 'pie' | 'scatter';
	title: string;
	display_order: number | null;
	sql_template: string;
	series_config: SeriesConfig[] | null;
	timeframe_type: 'days' | 'hours';
	timeframe_value: number;
	created_at: number;
	updated_at: number;
};

export type SavedItemCreate = {
	chat_id?: string;
	message_id: string;
	type: string;
	title: string;
	sql_template: string;
	series_config?: SeriesConfig[];
	timeframe_type: string;
	timeframe_value: number;
};

export type SavedItemUpdate = {
	title?: string;
	display_order?: number;
	series_config?: SeriesConfig[];
};

export type ChartSeries = {
	name: string;
	values: number[];
	color: string;
};

export type ChartData = {
	labels: string[];
	series: ChartSeries[];
	error?: string | null;
};

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Get all saved items for the current user
 */
export const getSavedItems = async (token: string): Promise<SavedItem[]> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/saved-items/`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch saved items' }));
		throw new Error(error.detail || 'Failed to fetch saved items');
	}

	return res.json();
};

/**
 * Check if a message has already been saved
 */
export const checkMessageSaved = async (token: string, messageId: string): Promise<boolean> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/saved-items/check/${messageId}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		// If check fails, assume not saved
		return false;
	}

	const data = await res.json();
	return data.saved;
};

/**
 * Get a specific saved item by ID
 */
export const getSavedItemById = async (token: string, itemId: string): Promise<SavedItem | null> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/saved-items/${itemId}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		if (res.status === 404) {
			return null;
		}
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch saved item' }));
		throw new Error(error.detail || 'Failed to fetch saved item');
	}

	return res.json();
};

/**
 * Create a new saved item
 */
export const createSavedItem = async (token: string, data: SavedItemCreate): Promise<SavedItem> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/saved-items/`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(data)
	});

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to save item' }));
		throw new Error(error.detail || 'Failed to save item');
	}

	return res.json();
};

/**
 * Update a saved item's title or display_order
 */
export const updateSavedItem = async (
	token: string,
	itemId: string,
	data: SavedItemUpdate
): Promise<SavedItem> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/saved-items/${itemId}`, {
		method: 'PATCH',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(data)
	});

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to update saved item' }));
		throw new Error(error.detail || 'Failed to update saved item');
	}

	return res.json();
};

/**
 * Delete a saved item
 */
export const deleteSavedItem = async (token: string, itemId: string): Promise<void> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/saved-items/${itemId}`, {
		method: 'DELETE',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to delete saved item' }));
		throw new Error(error.detail || 'Failed to delete saved item');
	}
};

/**
 * Reorder saved items by providing an ordered list of IDs
 */
export const reorderSavedItems = async (token: string, itemIds: string[]): Promise<void> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/saved-items/reorder`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ item_ids: itemIds })
	});

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to reorder items' }));
		throw new Error(error.detail || 'Failed to reorder items');
	}
};

/**
 * Get chart data for a saved item with a specific timeframe
 */
export const getMyStuffChartData = async (
	token: string,
	sqlTemplate: string,
	timeframeType: string,
	timeframeValue: number,
	seriesConfig?: SeriesConfig[]
): Promise<ChartData> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/my-stuff/chart-data`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			sql_template: sqlTemplate,
			timeframe_type: timeframeType,
			timeframe_value: timeframeValue,
			series_config: seriesConfig || []
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to load chart data' }));
		throw new Error(error.detail || 'Failed to load chart data');
	}

	return res.json();
};
