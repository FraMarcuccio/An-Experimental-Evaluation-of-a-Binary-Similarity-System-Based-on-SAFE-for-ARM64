import subprocess
import os

def build_and_run_docker_container():
    print("Building and starting the Docker container...")
    
    # Build the Docker image
    build_command = "docker build -t dockerresult -f Dockerfile ."
    result = subprocess.run(build_command, shell=True)
    if result.returncode != 0:
        print("Error during the container build.")
        return
    
    # Run the container in interactive mode
    run_command = "docker run --name my_docker_container -it dockerresult"
    print("Interactive execution of the container...")
    result = subprocess.run(run_command, shell=True)
    if result.returncode != 0:
        print("Error during the container startup.")
        return

def copy_file_from_container():
    print("Starting and copying files from the Docker container...")

    # Ensure that the my_docker_container has stopped
    check_container_command = "docker ps -q -a -f name=my_docker_container"
    result = subprocess.run(check_container_command, shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("The container my_docker_container is not present or has not stopped.")
        return

    # Copy files from the container to the current script path
    script_path = os.getcwd()  # Current folder of the script
    
    # Copy the metricsresult4files.json file
    copy_command_metrics = f"docker cp my_docker_container:/app/metricsresult4files.json {script_path}"
    result = subprocess.run(copy_command_metrics, shell=True)
    if result.returncode != 0:
        print("Error during the copy of metricsresult4files.json from the container.")
    else:
        print(f"File 'metricsresult4files.json' copied successfully to {script_path}.")

    # Copy the comparisonresult.json file
    copy_command_comparison = f"docker cp my_docker_container:/app/comparisonresult.json {script_path}"
    result = subprocess.run(copy_command_comparison, shell=True)
    if result.returncode != 0:
        print("Error during the copy of comparisonresult.json from the container.")
    else:
        print(f"File 'comparisonresult.json' copied successfully to {script_path}.")

    # Remove the container after the operation
    subprocess.run("docker rm -f my_docker_container", shell=True)

if __name__ == "__main__":
    # Builds and starts the Docker container in interactive mode
    build_and_run_docker_container()

    # Copies the metricsresult4files.json and comparisonresult.json files from the container to the local directory
    copy_file_from_container()

