export type Experiment = {
    id: number
    name: string
    modelName: string
    datasetName: string
    accuracy: number
    f1: number
    latencyMs: number
    cost: number
    status: string
}