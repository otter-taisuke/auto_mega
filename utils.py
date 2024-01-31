import collections
import glob
import os

import pandas as pd

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


def load_input(path: str) -> list[str] | None:
    for enc in ["utf-8", "shift-jis", "cp932"]:
        try:
            with open(path, "r", encoding=enc) as f:
                inputs = f.read().splitlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        print("Error: Not supported except text files for inputs.")
        return None
    if inputs is None:
        print(f"Error: Could not load \"{os.path.basename(path)}\" in utf-8, shift-jis, cp932.")
        return None
    return inputs


def pickup_same(exclude: bool = False):
    path = os.path.join(ROOT_DIR, "organism.txt")
    inputs = load_input(path)
    if exclude:
        print("same items:", [k for k, v in collections.Counter(inputs).items() if v > 1])
        write_list = [item + "\n" for item in list(dict.fromkeys(inputs))]
        write_list[-1] = write_list[-1].split()[0]
        write_list.remove("\n")
        with open(path, "w") as f:
            f.writelines(write_list)

    else:
        print("same items:", [k for k, v in collections.Counter(inputs).items() if v > 1])


def delete_finished(path: str = ""):
    organism = os.path.join(ROOT_DIR, "organism.txt")
    finished = os.path.join(ROOT_DIR, "finished_organism.txt")
    org_list = load_input(organism)
    fin_list = load_input(finished)
    if path != "":
        fin_list.extend(load_input(path))
    for org in fin_list:
        if org in org_list:
            org_list.remove(org)
    write_list = [item + "\n" for item in org_list]
    write_list[-1] = write_list[-1].split()[0]
    with open(organism, "w") as f:
        f.writelines(write_list)


def get_all_txt():
    txts = glob.glob(os.path.join(ROOT_DIR, "*", "*", "*.txt"))
    with open(os.path.join(ROOT_DIR, "finished_organism.txt"), mode="w") as f:
        for txt in txts:
            f.write(os.path.splitext(os.path.basename(txt))[0]+"\n")


def delete_blank(path: str = ""):
    with open(path, mode="r") as f:
        lines = f.readlines()
    with open(os.path.join(os.path.dirname(path), f"{os.path.splitext(os.path.basename(path))[0]}_delB.txt"), mode="w") as f:
        for line in lines:
            if line[0] == ">":
                spl = line.split(" ")
                f.write(spl[0]+"_"+" ".join(spl[1:]))
            else:
                f.write(line)


def make_fastq_from_excel(excel_path: str):
    output_dir = os.path.join(ROOT_DIR, "make_fastq_from_excel")
    query = os.path.splitext(os.path.basename(excel_path))[0]
    output_file = os.path.join(output_dir, query + ".txt")
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_excel(excel_path, sheet_name=0, header=0, index_col=None)
    df = df.fillna("")
    with open(output_file, mode="a") as f:
        for initials, protein, access, seq in zip(df["initials"], df["protein name"], df["accession number"], df["sequence"]):
            if protein == "":
                protein = "?"
            f.write(f">{initials}_{protein}_{access}\n{seq}\n\n")


def convert__2commma(txt_path: str):
    with open(txt_path, mode="r") as f:
        lines = f.readlines()
    with open(os.path.join(os.path.dirname(txt_path), f"{os.path.splitext(os.path.basename(txt_path))[0]}_comma.txt"), mode="w") as f:
        for line in lines:
            f.write(".".join(line.split("_")))


if __name__ == "__main__":
    # pickup_same(True)
    # get_all_txt()
    # delete_finished(r"C:\Users\nomur\Desktop\lab\auto_mega\blastp\NP_619732.2\no homology.txt")
    # delete_blank(r"C:\Users\nomur\desktop\lab\auto_mega\fastq_out\carti.txt")
    # make_fastq_from_excel(r"C:\Users\nomur\Desktop\Project - Slc26a13（能村）\2024 slc26a13.xlsx")
    convert__2commma(r"C:\Users\nomur\Desktop\lab\auto_mega\make_fastq_from_excel\2024 slc26a13.txt")
