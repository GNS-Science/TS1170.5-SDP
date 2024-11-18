<<<<<<< HEAD
# """
# The build module builds a final version.
#
# TODO:
#  - when `convert` and `versioning` packages are refactored, make this build more than just one version.
#
#
# Methods:
#     build_version_one: write out the outputs and record everything in new VersionInfo
# """
# from pathlib import Path
# from typing import Optional
#
# import pandas as pd
#
# from nzssdt_2023.config import RESOURCES_FOLDER
# from nzssdt_2023.convert import DistMagTable, SatTable
# from nzssdt_2023.versioning import ConvertedFile, IncludedFile, VersionInfo
#
#
# def build_version_one(description: Optional[str] = None) -> VersionInfo:
#     """Write out the outputs and record everything in new VersionInfo
#
#     Args:
#         description: the description of the version.
#     """
#
#     vi = VersionInfo(
#         version_number=1, nzshm_model_version="NSHM_v1.0.4", description=description
#     )
#
#     # build SAT files
#     in_path = Path(
#         RESOURCES_FOLDER, "pipeline", "v1", "SaT-variables_v5_corrected-locations.pkl"
#     )
#     df = pd.read_pickle(in_path)
#     sat = SatTable(df)
#
#     # SAT named
#     out_path = Path(RESOURCES_FOLDER, "v1", "named_locations.json")
#     sat.named_location_df().to_json(
#         out_path,
#         index=False,
#         orient="table",
#         indent=2,
#         double_precision=3,
#     )
#     vi.conversions.append(
#         ConvertedFile(
#             input_filepath=str(in_path.relative_to(RESOURCES_FOLDER)),
#             output_filepath=str(out_path.relative_to(RESOURCES_FOLDER)),
#         )
#     )
#     vi.manifest.append(IncludedFile(str(out_path.relative_to(RESOURCES_FOLDER))))
#
#     # SAT gridded
#     out_path = Path(RESOURCES_FOLDER, "v1", "grid_locations.json")
#     sat.grid_location_df().to_json(
#         out_path,
#         index=False,
#         orient="table",
#         indent=2,
#         double_precision=3,
#     )
#     vi.conversions.append(
#         ConvertedFile(
#             input_filepath=str(in_path.relative_to(RESOURCES_FOLDER)),
#             output_filepath=str(out_path.relative_to(RESOURCES_FOLDER)),
#         )
#     )
#     vi.manifest.append(IncludedFile(str(out_path.relative_to(RESOURCES_FOLDER))))
#
#     # D&M
#     in_path = Path(RESOURCES_FOLDER, "pipeline", "v1", "D_and_M_with_floor.csv")
#     dandm = DistMagTable(in_path)
#
#     out_path = Path(RESOURCES_FOLDER, "v1", "d_and_m.json")
#     dandm.flatten().to_json(
#         out_path,
#         index=True,
#         orient="table",
#         indent=2,
#     )
#     vi.conversions.append(
#         ConvertedFile(
#             input_filepath=str(in_path.relative_to(RESOURCES_FOLDER)),
#             output_filepath=str(out_path.relative_to(RESOURCES_FOLDER)),
#         )
#     )
#     vi.manifest.append(IncludedFile(str(out_path.relative_to(RESOURCES_FOLDER))))
#
#     # add remaining unmodified files to the manifest
#     for infile in [
#         "major_faults.geojson",
#         "urban_area_polygons.geojson",
#     ]:
#         in_path = Path(RESOURCES_FOLDER, "v1", infile)
#         vi.manifest.append(IncludedFile(str(in_path.relative_to(RESOURCES_FOLDER))))
#
#     return vi
#
#
# if __name__ == "__main__":
#     vi = build_version_one()
#     print(vi)
