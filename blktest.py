import subprocess
import argparse
import os
import shutil

def check_dependencies():
    """
    Check if requirements met.
    """
    required = ['fio', 'gnuplot']
    for dep in required:
        if not shutil.which(dep):
            raise RuntimeError(f"error: there's no {dep} installed.")

def run_test(name, filename, iodepth, rw):
    """
    Runs fio test with the specified settings and given iodepth and rw on a selected filename.
    """
    output_file = f"{name}_{rw}_iodepth{iodepth}.txt"
    command = [
        "fio",
        "--ioengine=libaio",
        "--direct=1",
        "--bs=4k",
        "--size=1G",
        "--numjobs=1",
        f"--name={name}",
        f"--filename={filename}",
        f"--rw={rw}",
        f"--iodepth={iodepth}",
        f"--output={output_file}"
    ]
    subprocess.run(command)
    return output_file

def test_result(output_file):
    """
    Parsing for latency result of fio test.
    """
    with open(output_file, 'r') as file:
        for line in file:
            if " lat (usec):" in line:
                parts = line.split()
                return float(parts[4].split('=')[1].replace(',', ''))
    return None

def generate_gnuplot(name, data, output_png):
    """
    Rendering of a plot for latency from IODepth.
    """
    script = f"""
    set terminal png size 800,600
    set output '{output_png}'
    set title "Latency vs IODepth for {name}"
    set xlabel "IODepth"
    set ylabel "Latency (usec)"
    set logscale x 2
    plot '-' with linespoints title 'randread', '-' with linespoints title 'randwrite'
    """
    for rw in ['randread', 'randwrite']:
        script += "\n".join(f"{iodepth} {latency}" for iodepth, latency in data[rw]) + "\ne\n"
    
    with open("plot.gnu", "w") as file:
        file.write(script)

    subprocess.run(["gnuplot", "plot.gnu"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-name", required=True, help="Name of the test")
    parser.add_argument("-filename", required=True, help="Path to the file to test")
    parser.add_argument("-output", required=True, help="Path to the output PNG file")
    args = parser.parse_args()

    if not os.access(args.filename, os.R_OK | os.W_OK):
        raise RuntimeError(f"error: no acces to {args.filename}. Make sure {args.filename} exists and you have access rights.")

    data = {'randread': [], 'randwrite': []}

    for iodepth in [2**i for i in range(0, 9)]:
        for rw in data.keys():
            output_file = run_test(args.name, args.filename, iodepth, rw)
            latency = test_result(output_file)
            if latency:
                data[rw].append((iodepth, latency))

    generate_gnuplot(args.name, data, args.output)

if __name__ == "__main__":
    main()