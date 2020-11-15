# Order Scheduler

This scheduler follows first come first serve (FCFS) strategy, with shortest job first (SCF) strategy for orders that lies in the same date. To reduce the average waiting time and prevent huge orders from blocking the pipeline for too long, "supply leak" strategy is used, where subsequent orders get part of the supply from the origin. If there are multiple origins available for fulfilling the order, the fulfillment priorities are based on the origin's estimated waiting time (The quotient of its average due order quantity and its history daily supply quantity).

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

