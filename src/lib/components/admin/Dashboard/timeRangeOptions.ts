export type TimeRangeOption = {
	value: string;
	label: string;
	rangeHours?: number;
	days?: number;
};

export const defaultRangeOptions: TimeRangeOption[] = [
	{ value: '1h', label: 'Last 1 hour', rangeHours: 1 },
	{ value: '6h', label: 'Last 6 hours', rangeHours: 6 },
	{ value: '12h', label: 'Last 12 hours', rangeHours: 12 },
	{ value: '24h', label: 'Last 24 hours', rangeHours: 24 },
	{ value: '7d', label: 'Last 7 days', days: 7 },
	{ value: '14d', label: 'Last 14 days', days: 14 },
	{ value: '30d', label: 'Last 30 days', days: 30 }
];

export const sidewallRangeOptions: TimeRangeOption[] = [
	{ value: '1h', label: 'Last 1 hour', rangeHours: 1 },
	{ value: '12h', label: 'Last 12 hours', rangeHours: 12 },
	{ value: '24h', label: 'Last 24 hours', rangeHours: 24 },
	{ value: '7d', label: 'Last 7 days', days: 7 }
];
