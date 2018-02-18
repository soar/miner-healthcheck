import argparse
import collections
import json
import platform
import socket
import time
import traceback
import requests
import sys


class MinerHealthCheck(object):

    SGMINER_HEALTHCHECK_CMD = '{"command":"devs"}'
    SGMINER_API_BUFFER_SIZE = 1024

    def __init__(self, cmdargs):
        self.args = cmdargs

        self.last_ifttt_report = time.time()

        self.gpu_errors_count = collections.defaultdict(int)
        self.low_activity_events_count = collections.defaultdict(int)

        self.miner_api_addr = '127.1'
        self.miner_api_port = 4028

    @property
    def ifttt_enabled(self):
        return bool(self.args.ifttt_action and self.args.ifttt_key)

    @property
    def periodic_checks_enabled(self):
        return bool(self.args.health_report_url)

    def run(self):
        while True:
            sgminer_healthy = True
            if self.args.sgminer:
                sgminer_healthy = self.check_sgminer()

            if sgminer_healthy:
                self.periodic_report()

            time.sleep(self.args.sleep)

    def periodic_report(self):
        try:
            r = requests.get(self.args.health_report_url)

            if self.args.debug:
                print(f"Periodic check sent, result: {r.status_code} = {r.text}")
        except Exception as ex:
            print(f"Exception occured: {ex}")

            if self.args.debug:
                print(f"Traceback: ")
                traceback.print_exc()

    def ifttt_report(self, event_name, message):
        if not self.ifttt_enabled:
            if self.args.ifttt_check:
                print("Requested check for IFTTT integration, but name and/or key not specified!")
            return

        if time.time() - self.last_ifttt_report <= 300:
            print(f"Last report was sent less than 5 minutes ago, skipping...")
            return

        url = f'https://maker.ifttt.com/trigger/{self.args.ifttt_action}/with/key/{self.args.ifttt_key}'
        try:
            r = requests.post(url, json={
                'value1': platform.node(),
                'value2': event_name,
                'value3': message
            })

            if self.args.debug:
                print(f"IFTTT report sent, result: {r.status_code} = {r.text}")
        except Exception as ex:
            print(f"Exception occured: {ex}")

            if self.args.debug:
                print(f"Traceback: ")
                traceback.print_exc()
        else:
            self.last_ifttt_report = time.time()

    def check_sgminer(self):
        sgminer_healthy = True
        raw_data = None
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.connect((self.miner_api_addr, self.miner_api_port))
            s.send(self.SGMINER_HEALTHCHECK_CMD.encode('ascii'))

            raw_data = bytes()
            raw_data_chunk = True
            while raw_data_chunk:
                raw_data_chunk = s.recv(self.SGMINER_API_BUFFER_SIZE)
                if raw_data_chunk:
                    raw_data += raw_data_chunk

            data = json.loads(raw_data[:-1], encoding='ascii')

            if self.args.debug:
                print("Got data from SGMiner:")
                print(json.dumps(data, indent=4, sort_keys=True))

            if not data.get('DEVS') or len(data.get('DEVS')) < 1:
                self.ifttt_report("no_devs_info", "Can't get information about GPUs")
            else:
                for dev_info in data.get('DEVS'):
                    sgminer_healthy &= self.check_gpu_health(dev_info)
        except Exception as ex:
            print(f"Exception occured: {ex}")

            self.ifttt_report("sgminer_check_fail", str(ex))

            if self.args.debug:
                print(f"Traceback: ")
                traceback.print_exc()
                print(f"Received RAW data: {raw_data}")

            sgminer_healthy = False
        finally:
            s.close()
            return sgminer_healthy

    def check_gpu_health(self, dev_info):
        dev_id = dev_info.get('GPU')
        if dev_id is None:
            self.ifttt_report("gpu_not_recognized", f"Got wrong GPU ID: {dev_id}")
            return False

        dev_enabled = dev_info.get('Enabled')
        if dev_enabled is None or not dev_enabled == 'Y':
            self.ifttt_report("gpu_disabled", f"GPU {dev_id} disabled")
            return False

        dev_activity = dev_info.get('GPU Activity')
        if dev_activity is None or not isinstance(dev_activity, int):
            self.ifttt_report("gpu_activity_wrong_info", f"GPU {dev_id} activity wrong info: {dev_activity}")
            return False
        if dev_activity < 70:
            if self.low_activity_events_count[dev_id] <= 3:
                self.low_activity_events_count[dev_id] += 1
            else:
                self.low_activity_events_count[dev_id] = 0
                self.ifttt_report("gpu_activity_too_low", f"GPU {dev_id} activity is {dev_activity}")
                return False

        dev_errors = dev_info.get('Hardware Errors')
        if dev_errors is None or not isinstance(dev_errors, int):
            self.ifttt_report("gpu_errors_wrong_info", f"GPU {dev_id} errors info: {dev_errors}")
            return False
        if dev_errors > self.gpu_errors_count[dev_id]:
            self.gpu_errors_count[dev_id] = dev_errors
            self.ifttt_report("gpu_has_errors", f"GPU {dev_id} has errors: {dev_errors}")
            return False

        dev_khashes_5s = dev_info.get('KHS 5s')
        if not dev_khashes_5s:
            self.ifttt_report("gpu_hashrate_failure", "No information found")
            return False
        elif dev_khashes_5s < self.args.gpu_hashrate_threshold:
            self.ifttt_report("gpu_hashrate_too_low", f"Device {dev_info.get('GPU')} hashrate {dev_khashes_5s} KHash/sec")
            return False

        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Miner HealthCheck")

    parser.add_argument('-d', '--debug', action='store_true', default=False, help="Enable verbose logging")

    parser.add_argument('--sleep', type=int, required=False, default=10, help="Time in seconds between checks")

    parser.add_argument('--health-report-url', type=str, required=True, help="URL to send periodic health reports")

    parser.add_argument('--sgminer', action='store_true', default=False, help="Enable checking Miner Health?")
    parser.add_argument('--gpu-hashrate-threshold', type=float, required=False, help="Send alert if hashrate is lower than, KHash/sec")

    parser.add_argument('--ifttt-check', action='store_true', help="Perform IFTTT check and exit")
    parser.add_argument('--ifttt-key', type=str, required=False, help="Secret key for IFTTT")
    parser.add_argument('--ifttt-action', type=str, required=False, default="miner_status", help="Action for IFTTT")

    args = parser.parse_args()

    m = MinerHealthCheck(args)

    print(f"Starting... Settings are:")
    print(f" - Periodic checks: {m.periodic_checks_enabled}")
    print(f" - IFTTT reports: {m.ifttt_enabled}")
    print(f" - SGMiner checks: {m.args.sgminer}")

    if args.ifttt_check:
        m.ifttt_report("check_integration", "success")
    else:
        try:
            m.run()
        except KeyboardInterrupt as ex:
            sys.exit(0)
