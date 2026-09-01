import { buses, events, kpiMetrics, trafficData, roadConditionData, systemAlerts } from '../data/mockData';

// Simulated API calls with delay to mimic real network latency

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export const getSystemAlerts = async () => {
  await delay(300);
  return systemAlerts;
};

export const getBuses = async () => {
  await delay(500);
  return buses;
};

export const getBusById = async (id) => {
  await delay(300);
  return buses.find(b => b.id === id);
};

export const getEvents = async () => {
  await delay(600);
  return events;
};

export const getEventById = async (id) => {
  await delay(300);
  return events.find(e => e.event_id === id);
};

export const getKPIMetrics = async () => {
  await delay(400);
  return kpiMetrics;
};

export const getTrafficAnalytics = async () => {
  await delay(700);
  return trafficData;
};

export const getRoadConditionAnalytics = async () => {
  await delay(700);
  return roadConditionData;
};
