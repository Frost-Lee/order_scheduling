# Order Scheduler

This scheduler follows first come first serve (FCFS) strategy, with shortest job first (SJF) strategy for orders that lies in the same date. To reduce the average waiting time and prevent huge orders from blocking the pipeline for too long, "supply leak" strategy is used, where subsequent orders get part of the supply from the origin. If there are multiple origins available for fulfilling the order, the fulfillment priorities are based on the origin's estimated waiting time (The quotient of its average due order quantity and its history daily supply quantity).

## Run the Frontend App

``` bash
yarn start
```

## Run the Backend App

``` bash
python api/app.py
```

## Unit Test Backend

``` bash
cd api/
python -m unittest
```

## What's the Next Step

### Algorithm

- [ ] Do more optimization by taking future supply plan data into consideration
- [ ] Try solving the optimization problem with heuristic algorithm (eg. genetic algorithm)
- [ ] More test data and more performance evaluation metrics
- [ ] Use specific distribution (eg. poisson distribution for generating order dates) to generate more "real" stress test data

### Backend

- [ ] Return the remaining order data if some orders are not fulfilled

### Frontend

- [ ] Display the remaining order data if some orders are not fulfilled
- [ ] Enable drag and drop for uploading file, enable uploading multiple files at the same time
- [ ] Provide more information if the file format is incorrect