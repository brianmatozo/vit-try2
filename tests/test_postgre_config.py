from pathlib import Path

import yaml


class TestPostgreConfig:
    def test_postgre_conf_exists_and_valid(self):
        conf_path = Path("postgre.conf")
        assert conf_path.exists(), "postgre.conf must exist in project root"

        lines = conf_path.read_text().splitlines()
        settings = {}
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            assert "=" in line, f"Invalid configuration line: {line}"
            key, val = line.split("=", 1)
            settings[key.strip()] = val.strip()

        # Check critical settings
        assert settings["listen_addresses"] in ("'*'", "*")
        assert settings["max_connections"] == "50"
        assert settings["shared_buffers"] == "2GB"
        assert settings["effective_cache_size"] == "6GB"
        assert settings["checkpoint_completion_target"] == "0.9"

    def test_postgre_prod_conf_compatibility(self):
        prod_conf = Path("postgre.prod.conf")
        assert prod_conf.exists(), "postgre.prod.conf symlink or file must exist"
        # Must resolve to postgre.conf
        assert prod_conf.resolve() == Path("postgre.conf").resolve()

    def test_docker_compose_config_validity(self):
        dc_path = Path("docker-compose.yaml")
        assert dc_path.exists(), "docker-compose.yaml must exist"

        content = yaml.safe_load(dc_path.read_text())
        assert "services" in content
        assert "postgres" in content["services"]
        pg = content["services"]["postgres"]

        # Ensure image is postgres 18
        assert "postgres:18" in pg["image"]

        # Ensure ports are mapped
        assert "ports" in pg
        assert any("5432" in str(p) for p in pg["ports"])

        # Ensure shm_size is set to accommodate 2GB shared_buffers
        assert "shm_size" in pg
        assert pg["shm_size"] in ("2gb", "2g", "2GB", "2G")

        # Ensure volume mounts postgre.conf
        volumes = pg.get("volumes", [])
        has_conf_mount = any("postgre.conf" in v for v in volumes)
        assert has_conf_mount, f"Expected postgre.conf mount in volumes: {volumes}"
