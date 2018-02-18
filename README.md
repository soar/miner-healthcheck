# Health Check Script

## Installation

### 1. Enable API in SGMiner

If you don't want SGMiner checks or use different miner - disable this feature (don't use `--sgminer` key).

To enable SGMiner API add following parameters to `sgminer.exe` command-line:

```
sgminer.exe --api-listen <your-other-parameters>
```

### 2. Download fresh version

You can get it from:
* Releases page: [https://github.com/soar/miner-healthcheck/releases]()
* Yandex.Disk: https://yadi.sk/d/x70GZTrP3RaGsC/tools/healthcheck

### 3. Get keys

You need two keys:

#### StatusCake Integration

Each started instance of `miner-healthcheck` will send push messages to this URL every X seconds. If StatusCake won't receive this messages for some time - you will get notification.

So this is check - is your RIG alive or not?

How to get your `STATUSCAKE_PUSH_URL`: [https://github.com/soar/miner-healthcheck/wiki/StatusCake-Integration]()

#### IFTTT Integration

When your RIG have some troubles - push notification will be sent to IFTTT webhook URL. This URL is common for all your RIGs.

How to get your `YOUR_IFTTT_WEBHOOK_KEY`: [https://github.com/soar/miner-healthcheck/wiki/IFTTT-Integration]()

### 4. First run and check

Perform test running with next command line:

```
miner-healthcheck.exe ^
    --health-report-url "STATUSCAKE_PUSH_URL" ^
    --ifttt-check ^
    --ifttt-key YOUR_IFTTT_WEBHOOK_KEY
```

If test was successful - you should see message in Telegram:

```
Event: check_integration
Message: success
```

### 5. Run in production mode

```
miner-healthcheck.exe ^
    --health-report-url "STATUSCAKE_PUSH_URL" ^
    --ifttt-key YOUR_IFTTT_WEBHOOK_KEY ^
    --sgminer ^
    --gpu-hashrate-threshold 0.3 
```

## Logic

1. Script should be started at system startup
2. It has infinite loop and runs forever
3. Every X seconds - it performs checks:
    - if SGMiner checks are enabled:
        - SGMiner is alive
        - SGMiner answers on API requests
        - Each GPU is alive
        - GPUs hash-rate is above threshhold
4. If checks passed successfully - it makes remote HTTP request to report about it health to `STATUSCAKE_PUSH_URL`
5. If remote endpoint doesn't receive health check report in Y seconds - StatusCake sends notification to configured targets (see Web-UI for settings)
	
## Parameters

- `--help` - show help
- `--debug` - show debug messages (not recommended for every-day use)
- `--sleep X` - time between checks, 10 seconds by default, recommended
- `--sgminer` - enable specific checks for SGMiner (via API, see Installation)
- `--gpu-hashrate-threshold X.X` - when one of installed GPUs will gave hashrate lower, than this value (in KHash/sec) - notification will be sent

### Examples

```
miner-healthcheck.exe --health-report-url "https://push.statuscake.com/?PK=XXXXXXXX&TestID=00000&time=0" --sgminer --gpu-hashrate-threshold 0.36 --ifttt-key lk9y6DOXXXXXXXXX
```

## Building

```
pyinstaller --onefile --icon miner.ico --name miner-healthcheck-v1.2.exe run.py
```	
