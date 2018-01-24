# Health Check Script

## Installation

### 1. Enable API in SGMiner

If you don't want SGMiner checks or use different miner - disable this feature (don't use `--sgminer` key).

To enable SGMiner API add following parameters to `sgminer.exe` command-line:

```
sgminer.exe --api-listen <your-other-parameters>
```

### 2. Download fresh version

It's located here: https://yadi.sk/d/x70GZTrP3RaGsC/tools/healthcheck

### 3. Get keys

You need two keys:

- `MONITORING_URL`/`UNIQUE_MONITORING_KEY` - this is unique part of monitoring URL, where periodic checks are sent
- `COMMON_NOTIFICATION_KEY` - this is key for reporting, it is common between mining rigs/PCs

You can get both by asking @soar.

### 4. First run and check

Perform test running with next command line:

```
miner-healthcheck.exe ^
    --health-report-url "https://MONITORING_URL/UNIQUE_MONITORING_KEY" ^
    --ifttt-check ^
    --ifttt-key COMMON_NOTIFICATION_KEY
```

If test was successful - you should see message in Telegram:

```
Event: check_integration
Message: success
```

### 5. Run in production mode

```
miner-healthcheck.exe ^
    --health-report-url "https://MONITORING_URL/UNIQUE_MONITORING_KEY" ^
    --ifttt-key COMMON_NOTIFICATION_KEY ^
    --sgminer ^
    --gpu-hashrate-threshold 0.3 
```

## Logic

1. Script should be started at system startup
2. It has infinite loop and runs forever
3. Every X seconds - it performs checks:
	- SGMiner is alive
	- SGMiner answers on API requests
	- Each GPU is alive
	- GPUs hash-rate is above threshhold
4. If checks passed successfully - it makes remote HTTP request to report about it health
5. If remote endpoint doesn't receive health check report in Y seconds - it sends notification to:
	- Telegram Chat *Miners*
	- Email *i@soar.name*
	- Optional notifications may be added
	
## Parameters

- `--help` - show help
- `--debug` - show debug messages (not recommended for every-day use)
- `--sleep X` - time between checks, 10 seconds by default, recommended
- `--sgminer` - enable specific checks for SGMiner (via API, see Installation)
- `--gpu-hashrate-threshold X.X` - when one of installed GPUs will gave hashrate lower, than this value (in KHash/sec) - notification will be sent

### Examples

```
miner-healthcheck.exe --health-report-url "https://MONITORING_URL/UNIQUE_MONITORING_KEY" --ifttt-key COMMON_NOTIFICATION_KEY --gpu-hashrate-threshold 0.3 --sgminer
```
	
