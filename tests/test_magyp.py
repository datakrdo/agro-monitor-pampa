from agro.magyp import cargar_estimaciones

CSV = """cultivo,anio,campania,provincia,provincia_id,departamento,departamento_id,superficie_sembrada_ha,superficie_cosechada_ha,produccion_tm,rendimiento_kgxha
soja total,2023,2023/2024,Buenos Aires,06,Pergamino,6623,150000,148000,370000,2500
trigo total,2023,2023/2024,Buenos Aires,06,Pergamino,6623,80000,79000,240000,3038
soja total,2023,2023/2024,Santa Fe,82,Belgrano,82014,90000,88000,220000,2500
ajo,2023,2023/2024,Buenos Aires,06,Pergamino,6623,3,3,10,3333
"""


def test_cargar_estimaciones_filtra_cultivo_y_zero_pad(tmp_path):
    csv_path = tmp_path / "estimaciones.csv"
    csv_path.write_text(CSV)

    out = cargar_estimaciones(str(csv_path), "soja total")

    assert len(out) == 2
    assert set(out["depto_id"]) == {"06623", "82014"}  # zero-padded a 5 dígitos
    assert "ajo" not in out.columns  # se descartó junto con las columnas no usadas


def test_cargar_estimaciones_filtra_por_region(tmp_path):
    csv_path = tmp_path / "estimaciones.csv"
    csv_path.write_text(CSV)

    out = cargar_estimaciones(str(csv_path), "soja total", depto_ids={"06623"})

    assert list(out["depto_id"]) == ["06623"]
