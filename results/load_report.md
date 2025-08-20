# Load Test Report
**Timestamp:** 1755726587
**Test Duration:** 2.1s

## Configuration
- Concurrency: 2 workers
- Episodes per worker: 5
- Total episodes: 10
- Prompt: 'search for load testing'

## Results
- Successful workers: 2/2 (100.0%)
- Average worker duration: 2.0s
- Episodes per second: 4.80

## Recommendations
- Max stable concurrency: 2
- Typical resource usage: Monitor with `docker stats` or k8s metrics
- Bottlenecks: None detected

**Detailed results:** `load_test_1755726587.json`