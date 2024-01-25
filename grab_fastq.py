import argparse
from glob import glob
import os
import shutil

import openpyxl as pyxl


ROOT = os.path.abspath(os.path.dirname(__file__))
INPUT_DIR = os.path.join(ROOT, "blast")
OUTPUT_DIR = os.path.join(ROOT, "fastq_out")
DEFAULT_QUERY = "query.txt"


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grab selected Sequence in fastq.")
    parser.add_argument("-q", "--query", default=DEFAULT_QUERY)
    parser.add_argument("-i", "--input", default=INPUT_DIR)
    parser.add_argument("-o", "--output", default=OUTPUT_DIR)
    args = parser.parse_args()
    return args


def load_input(path: str) -> list[str] | None:
    ext = os.path.splitext(path)[1]
    inputs: list[str] | None = None
    if ext == ".txt":
        for enc in ["utf-8", "shift-jis", "cp932"]:
            try:
                with open(path, "r", encoding=enc) as f:
                    inputs = f.read().splitlines()
                break
            except UnicodeDecodeError:
                continue
    else:
        print("Error: Not supported file type.")
        return None
    if inputs is None:
        print(f"Error: Could not load \"{os.path.basename(path)}\" in utf-8, shift-jis, cp932.")
        return None
    return inputs


def write_excel(excel_path: str, datas: list[list[str]]):
    wb = pyxl.load_workbook(excel_path)
    ws = wb.active
    for i, data in enumerate(datas):
        ws.append(data[i])
    wb.save(excel_path)


def parse_fastq(path: str) -> None | dict:
    lines = load_input(path)
    if lines is None:
        return None
    seq_dict = {}
    former_seq = ""
    for line in lines:
        if line[0] == '>':
            seq_dict[line.splitlines()[0]] = ""
            former_seq = line.splitlines()[0]
        else:
            seq_dict[former_seq] += line.splitlines()[0]
    return seq_dict


def search_accessions(accessions: list, query: str) -> int | None:
    choices = []
    for accession in accessions:
        if query in accession:
            choices.append(accession)
    print(choices)
    if len(choices) != 1:
        return None
    for i, accession in enumerate(accessions):
        if accession == choices[0]:
            return i


def grab_fastq(args: argparse.Namespace):
    os.makedirs(args.output, exist_ok=True)
    query_lines = load_input(os.path.join(ROOT, args.query))
    for query_line in query_lines:
        query = query_line.split(",")[0]
        fastq_dir = os.path.join(ROOT, "blast", query)
        fastq_files = glob(os.path.join(fastq_dir, "*.txt"))
        for fastq in fastq_files:
            seq_dict = parse_fastq(fastq)
            species = os.path.splitext(os.path.basename(fastq))[0]
            accessions = []
            seq_keys = list(seq_dict.keys())
            for info in seq_keys:
                elements = info.split(" ")
                accessions.append(elements[0][1:])
            print(f"------------- <{species}> -------------")
            for i, accession in enumerate(accessions):
                print(f"{i+1}: {accession}")
            choosed_nums = []
            flag = ""
            while flag != "y":
                input_num = input("enter number(with n like n4) or accession num with blank separator.\n : ").split(" ")
                if input_num[0] == "all":
                    input_num = accessions
                    break
                elif input_num[-1] == "ex":
                    flag = input(f"you enter {len(accessions)-len(input_num)+1}th number. Correct? (y/n)\n : ")
                else:
                    flag = input(f"you enter {len(input_num)}th number. Correct? (y/n)\n : ")
            for i, num in enumerate(input_num):
                if num == "ex":
                    if i+1 == len(input_num):
                        choosed_nums = list(set(range(len(accessions)))-set(choosed_nums))
                        continue
                if "n" not in num:
                    inp_n = num
                    choices = search_accessions(accessions, inp_n)
                    while choices is None:
                        inp_n = input(f"<{inp_n}> There are no unique choice. Enter accurate number: ")
                        choices = search_accessions(accessions, inp_n)
                    choosed_nums.append(choices)
                elif "n" in num and len(accessions) >= int(num[1:]):
                    choosed_nums.append(int(num[1:]))
                else:
                    n = "n10000000"
                    while len(accessions) >= int(n[1:]):
                        n = input("invalid number(with n). Enter accurate number(with n): ")
                    choosed_nums.append(int(n[1:]))
            print(choosed_nums)

            # with open(os.path.join(args.output, query + ".txt"), mode="a") as f:
            #     for num in choosed_nums:
            #         f.write(">" + "_".join(species.split(" ")) + "_" + seq_keys[int(num)-1][1:] + "\n")
            #         f.write(seq_dict[seq_keys[int(num)-1]] + "\n\n")




if __name__ == "__main__":
    args = get_arguments()
    grab_fastq(args)
