import type { Experiment } from '../types/experiment'

export const mockExperiments: Experiment[] = [
    {
        id: 1,
        name: '实验1',
        modelName: 'deepseek-chat',
        datasetName: 'eval-set-a',
        accuracy: 0.91,
        f1: 0.87,
        latencyMs: 820,
        cost: 1.24,
        status: 'completed',
    },
    {
        id: 2,
        name: '实验2',
        modelName: 'deepseek-chat',
        datasetName: 'eval-set-b',
        accuracy: 0.88,
        f1: 0.82,
        latencyMs: 960,
        cost: 1.41,
        status: 'completed',
    },
    {
        id: 3,
        name: '实验3',
        modelName: 'qwen-plus',
        datasetName: 'eval-set-a',
        accuracy: 0.84,
        f1: 0.79,
        latencyMs: 730,
        cost: 1.08,
        status: 'running',
    },
]