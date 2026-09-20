import os
import sys
from collections import defaultdict


# ============================================================
# PROJECT PATH
# ============================================================

ROOT_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

SRC_DIR = os.path.join(
    ROOT_DIR,
    "src"
)

if SRC_DIR not in sys.path:
    sys.path.insert(
        0,
        SRC_DIR
    )


from PIL import Image
from app import detect_issue


# ============================================================
# BENCHMARK DATASET LOCATION
# ============================================================

BENCHMARK_DIR = os.path.join(
    ROOT_DIR,
    "tests",
    "ai_samples"
)


# ============================================================
# EXPECTED FOLDER -> EXPECTED AI LABEL
# ============================================================

CATEGORIES = {

    "pothole":
        "Pothole / Road Damage",

    "garbage":
        "Garbage Dump / Litter",

    "overflowing_dustbin":
        "Overflowing / Unclean Dustbin",

    "open_manhole":
        "Open Manhole / Open Drain",

    "blocked_drain":
        "Blocked / Overflowing Drain",

    "sewage_overflow":
        "Sewage / Storm-Water Overflow",

    "waterlogging":
        "Stagnant Water / Waterlogging",

    "construction_debris":
        "Construction / Demolition Debris",

    "burning_waste":
        "Burning Garbage / Waste",

    "dead_animal":
        "Dead Animal",

    "broken_streetlight":
        "Broken Streetlight",

    "damaged_footpath":
        "Damaged Footpath / Public Path",

    "fallen_tree":
        "Fallen Tree / Road Obstruction",

    "broken_signal":
        "Broken Traffic Signal",

    "no_civic_issue":
        "No Clear Civic Issue"
}


VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


# ============================================================
# CREATE DATASET FOLDERS AUTOMATICALLY
# ============================================================

def ensure_dataset_structure():

    os.makedirs(
        BENCHMARK_DIR,
        exist_ok=True
    )

    for folder_name in CATEGORIES:

        folder_path = os.path.join(
            BENCHMARK_DIR,
            folder_name
        )

        os.makedirs(
            folder_path,
            exist_ok=True
        )


# ============================================================
# GET IMAGES
# ============================================================

def get_images(folder_path):

    images = []

    if not os.path.exists(
        folder_path
    ):
        return images


    for filename in sorted(
        os.listdir(folder_path)
    ):

        extension = os.path.splitext(
            filename
        )[1].lower()


        if extension in VALID_EXTENSIONS:

            images.append(
                os.path.join(
                    folder_path,
                    filename
                )
            )


    return images


# ============================================================
# RUN BENCHMARK
# ============================================================

def run_benchmark():

    ensure_dataset_structure()


    print(
        "\n============================================"
    )

    print(
        " CIVICROUTE AI IMAGE BENCHMARK"
    )

    print(
        "============================================"
    )


    total_images = 0
    total_correct = 0

    category_total = defaultdict(int)
    category_correct = defaultdict(int)

    failures = []


    for folder_name, expected_label in CATEGORIES.items():

        folder_path = os.path.join(
            BENCHMARK_DIR,
            folder_name
        )


        image_paths = get_images(
            folder_path
        )


        if not image_paths:

            print(
                f"[NO DATA] {folder_name}"
            )

            continue


        print(
            f"\n--- {expected_label} ---"
        )


        for image_path in image_paths:

            total_images += 1

            category_total[
                folder_name
            ] += 1


            filename = os.path.basename(
                image_path
            )


            try:

                image = Image.open(
                    image_path
                ).convert("RGB")


                result = detect_issue(
                    image
                )


                predicted = result[
                    "issue"
                ]

                confidence = round(
                    result[
                        "confidence"
                    ] * 100,
                    1
                )


                passed = (
                    predicted == expected_label
                )


                if passed:

                    total_correct += 1

                    category_correct[
                        folder_name
                    ] += 1

                    status = "PASS"

                else:

                    status = "FAIL"

                    failures.append({
                        "file":
                            filename,

                        "expected":
                            expected_label,

                        "predicted":
                            predicted,

                        "confidence":
                            confidence
                    })


                print(
                    f"[{status}] "
                    f"{filename}"
                )

                print(
                    f"       Expected:   "
                    f"{expected_label}"
                )

                print(
                    f"       Predicted:  "
                    f"{predicted}"
                )

                print(
                    f"       Confidence: "
                    f"{confidence}%"
                )


            except Exception as error:

                failures.append({
                    "file":
                        filename,

                    "expected":
                        expected_label,

                    "predicted":
                        "ERROR",

                    "confidence":
                        0
                })


                print(
                    f"[ERROR] {filename}"
                )

                print(
                    f"        {error}"
                )


    # ========================================================
    # NO DATA = BENCHMARK NOT VALID
    # ========================================================

    print(
        "\n============================================"
    )

    print(
        " AI BENCHMARK SUMMARY"
    )

    print(
        "============================================"
    )


    if total_images == 0:

        print(
            "STATUS: INCOMPLETE"
        )

        print(
            "No benchmark images were found."
        )

        print(
            "\nDataset folders have now been created at:"
        )

        print(
            BENCHMARK_DIR
        )

        print(
            "\nAdd independently labelled real civic "
            "complaint photos before claiming AI accuracy."
        )

        return 2


    # ========================================================
    # PER CATEGORY
    # ========================================================

    for folder_name, expected_label in CATEGORIES.items():

        total = category_total[
            folder_name
        ]

        correct = category_correct[
            folder_name
        ]


        if total == 0:
            continue


        accuracy = (
            correct / total
        ) * 100


        print(
            f"{expected_label:<40} "
            f"{correct}/{total} "
            f"({accuracy:.1f}%)"
        )


    overall_accuracy = (
        total_correct / total_images
    ) * 100


    print(
        "--------------------------------------------"
    )

    print(
        f"TOTAL IMAGES:       {total_images}"
    )

    print(
        f"CORRECT:            {total_correct}"
    )

    print(
        f"INCORRECT:          "
        f"{total_images - total_correct}"
    )

    print(
        f"OVERALL ACCURACY:   "
        f"{overall_accuracy:.1f}%"
    )

    print(
        "============================================"
    )


    # ========================================================
    # FAILED CASES
    # ========================================================

    if failures:

        print(
            "\nFAILED / AMBIGUOUS CASES"
        )

        print(
            "--------------------------------------------"
        )


        for failure in failures:

            print(
                f"{failure['file']}"
            )

            print(
                f"  Expected : "
                f"{failure['expected']}"
            )

            print(
                f"  Predicted: "
                f"{failure['predicted']}"
            )

            print(
                f"  Confidence: "
                f"{failure['confidence']}%"
            )


    # ========================================================
    # BENCHMARK STATUS
    # ========================================================

    print(
        "\nIMPORTANT:"
    )

    print(
        "This benchmark measures classification "
        "accuracy only on the labelled images supplied."
    )

    print(
        "It does not prove universal real-world accuracy."
    )


    if overall_accuracy >= 80:

        print(
            "\nSTATUS: BENCHMARK PASSED"
        )

        return 0


    print(
        "\nSTATUS: BENCHMARK NEEDS IMPROVEMENT"
    )

    return 1


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    sys.exit(
        run_benchmark()
    )