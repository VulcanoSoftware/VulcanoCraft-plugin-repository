import subprocess
import json
import os

def run_test(url, expected_loaders):
    """Runs a test case for the plugin_loaders script."""
    try:
        # Pass the CURSEFORGE_API_KEY to the subprocess environment
        env = os.environ.copy()
        result = subprocess.run(
            ['.venv/bin/python', 'fetchers/plugin_loaders.py', url],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        output = json.loads(result.stdout.strip())
        assert set(output) == set(expected_loaders), f"Test failed for {url}. Expected {expected_loaders}, got {output}"
        print(f"Test passed for {url}")
    except (subprocess.CalledProcessError, json.JSONDecodeError, AssertionError) as e:
        print(f"Test failed for {url}: {e}")
        # Print stderr for more details on the error
        if isinstance(e, subprocess.CalledProcessError):
            print(f"Stderr: {e.stderr}")


def main():
    # Test cases
    run_test("https://www.spigotmc.org/resources/essentialsx.9089/", ["1.8", "1.9", "1.10", "1.11", "1.12", "1.13", "1.14", "1.15", "1.16", "1.17", "1.18", "1.19", "1.20", "1.21"])
    run_test("https://hangar.papermc.io/PaperMC/Velocity", [])

    # This test will only pass if a valid CURSEFORGE_API_KEY is set as an environment variable
    if os.environ.get("CURSEFORGE_API_KEY"):
        run_test("https://www.curseforge.com/minecraft/mc-mods/jei", ["Forge", "Fabric", "Quilt"])
    else:
        print("Skipping CurseForge test because CURSEFORGE_API_KEY is not set.")

if __name__ == "__main__":
    main()
