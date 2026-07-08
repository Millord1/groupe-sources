from multiprocessing import Pool
import subprocess
import sys

scripts = [ "eau.py", "geo_risque.py", "dvf.py","reseau_eaux.py"]

def run_script(script_name):
   
    return subprocess.run([sys.executable, script_name], capture_output=True, text=True)

if __name__ == "__main__":
    with Pool(processes=len(scripts)) as pool:
        results = pool.map(run_script, scripts)
        
    for script, res in zip(scripts, results):
        if res.returncode == 0:
            print(f"{script} done.")
        else:
            print(f"{script} failed:\n{res.stderr}")
    subprocess.run([sys.executable, "analyses.py"])