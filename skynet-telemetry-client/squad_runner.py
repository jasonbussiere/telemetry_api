import argparse
import subprocess
import sys
import time

def main():
    parser = argparse.ArgumentParser(description='Telemetry Squad Simulator launcher')
    parser.add_argument('--count',type=int, default=1, help='Number of virtual agents to simulate (default: 1)')
    args = parser.parse_args()
    agent_count = args.count
    processes = []

    print(f"Launching a squad of {agent_count} simulated telemetry agents")

    with open("telemetry.log","a") as log_file:
        try:
            for i in range(1,agent_count+1):
                #redirige output vers un log file
                process=subprocess.Popen([sys.executable, "-u", "T850_agent.py", "--id", str(i)],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                )
                processes.append(process)
                time.sleep(0.5)

            print("=========================================")
            print(f"All {agent_count} agents are now running!")
            print("Press [CTRL+C] to stop the simulation.")
            print("=========================================")

            for p in processes:
                p.wait()

        except KeyboardInterrupt:
            print("\n Stopping all simulated agents...")
            for p in processes:
                p.terminate()
            print("\n[CTRL+C detected] All agents stopped")



if __name__ == "__main__":
    main()