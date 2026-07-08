import load
import contextlib

class Analytic:
    def __init__(self):
        self.conn = load.connect()
        
    @contextlib.contextmanager
    def _create_scope(self):
        conn = load.connect()
        
        try:
            with conn.cursor() as cur:
                yield cur
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_all_tables(self) -> list:
        q = """        
        SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        with self._create_scope() as cur:
            cur.execute(q)
            return [row[0] for row in cur.fetchall()]
        
    def get_all_filtered_tables(self) -> list:
        all_tables = self.get_all_tables()
        tables_to_exclude = {'region', 'departement', 'commune', 'gare', 'entreprise_btp'}
        filtered_tables = [t for t in all_tables if t not in tables_to_exclude]
        return filtered_tables
    
    
    def get_primary_key(self, table: str) -> str:
        match table:
            case 'dechets_radioactifs':
                return "nom_du_site"
            case 'clubs_boxe_thai':
                return "id::text"
            case 'bibliotheque':
                return "code_bib"
            case 'college', 'lycee':
                return 'uai'
            case 'ehpad', 'pharmacie':
                return 'finess'
            case 'mairie':
                return 'insee_code'
            case _:
                return "name"
        
    def count_all_tables(self):
        all_tables = self.get_all_tables()
        results = {}
        
        with self._create_scope() as cur:
            for table in all_tables:
                q = f"SELECT COUNT(*) FROM {table};"
                
                try:
                    cur.execute(q)
                    count = cur.fetchone()[0]
                    results[table] = count
                except Exception as e:
                    print(f"Error count {table} : {e}")
                    continue
                    
        return results
    
    def get_communes_by_region_and_dep(self):
        # ROLLUP = dinguerie !!
        q = """
        SELECT 
            r.name AS region_name, d.name AS dep_name, COUNT(c.insee_code) AS total_communes
        FROM commune AS c
        INNER JOIN departement AS d ON c.code_departement = d.code_departement
        INNER JOIN region AS r ON d.code_region = r.code_region
        GROUP BY ROLLUP(r.name, d.name)
        ORDER BY r.name NULLS LAST, d.name NULLS LAST;
        """
        res = None
        with self._create_scope() as cur:
            try:
                cur.execute(q)
                res = cur.fetchall()
            except Exception as e:
                print(f"Error communes by region and dep: {e}")
        return res
    
    def get_all_things_by_dept(self):
        filtered_tables = self.get_all_filtered_tables()
        
        all_res = list()
        
        with self._create_scope() as cur:
            for table in filtered_tables:
                q = f"""
                SELECT '{table}' AS table_name, count(t.*) AS total, c.code_departement AS code_dept FROM {table} AS t
                INNER JOIN commune AS c ON t.insee_code = c.insee_code
                GROUP BY c.code_departement
                """
                
                try:
                    cur.execute(q)
                    res = cur.fetchall()
                    all_res.extend(res)
                except Exception as e:
                    print(f"Error get all things: {e}")
                    continue
                
        return all_res
    
    def get_total_population(self):
        q = """
        SELECT r.name AS region_name, d.name AS dept_name, SUM(c.population) as total_population
        FROM commune AS c
        INNER JOIN departement AS d ON c.code_departement = d.code_departement
        INNER JOIN region AS r ON d.code_region = r.code_region
        GROUP BY ROLLUP(r.name, d.name)
        """

        with self._create_scope() as cur:
            try:
                cur.execute(q)
                res = cur.fetchall()
                return res
            except Exception as e:
                print(f"Error total population: {e}")
                
        
    def get_dept_with_more_pharmacie(self):
        q = """
        SELECT COUNT(p.finess) as total_pharmacie, d.name as dept_name, d.code_departement as dept_code
        FROM pharmacie AS p
        INNER JOIN commune AS c ON p.insee_code = c.insee_code
        INNER JOIN departement AS d ON c.code_departement = d.code_departement
        GROUP BY d.name, d.code_departement
        ORDER BY total_pharmacie DESC
        """
    
        with self._create_scope() as cur:
            try:
                cur.execute(q)
                res = cur.fetchall()
                return res
            except Exception as e:
                print(f"Error total population: {e}")
                
    def get_mean_etab_by_commune_in_dept(self):
        filtered_tables = self.get_all_filtered_tables()
        
        all_res = list()
        
        for table in filtered_tables:
            # q1 = f"""
            # SELECT AVG(COUNT(*)) as mean_etab, c.name as commune_name, d.name as dept_name
            # FROM {table} as t
            # INNER JOIN commune AS c ON t.insee_code = c.insee_code
            # INNER JOIN departement AS d ON c.code_departement = d.code_departement
            # GROUP BY c.name, d.name
            # """
            
            q = f"""
            WITH count_etab AS (
                SELECT c.code_departement, c.insee_code, c.name AS commune_name, COUNT(t.*) AS total_etab
                FROM commune AS c
                LEFT JOIN {table} AS t ON c.insee_code = t.insee_code
                GROUP BY c.code_departement, c.insee_code
            )
            
            SELECT ROUND(AVG(ce.total_etab), 1) as mean_etab , '{table}' AS table_name, d.name as dept_name, ce.commune_name
            FROM count_etab AS ce
            INNER JOIN departement AS d ON ce.code_departement = d.code_departement
            GROUP BY d.name, ce.commune_name
            ORDER BY d.name
            """
            
            with self._create_scope() as cur:
                try:
                    cur.execute(q)
                    res = cur.fetchall()
                    all_res.extend(res)
                except Exception as e:
                    print(f"Error during mean etab: {e}")
                    continue
            
        # for res in all_res:
        #     if res[0] > 0:
        #         print(res)
        return all_res
    
    # 3.1
    def get_commune_with_lycee_no_pharmacie(self):
        q1 = """
            SELECT c.name AS commune_name, COUNT(DISTINCT l.uai) AS total_lycee 
            FROM commune AS c
            INNER JOIN lycee AS l ON c.insee_code = l.insee_code
            LEFT JOIN pharmacie AS p ON c.insee_code = p.insee_code
            GROUP BY c.insee_code, c.name
            HAVING COUNT(p.insee_code) = 0;
            """
        
        q = """
            SELECT c.name AS commune_name, COUNT(DISTINCT l.uai) AS total_lycee 
            FROM commune AS c
            INNER JOIN lycee AS l ON c.insee_code = l.insee_code
            WHERE NOT EXISTS (
                SELECT 1 
                FROM pharmacie AS p 
                WHERE p.insee_code = c.insee_code
            )
            GROUP BY c.insee_code, c.name;
        """
        
        
        with self._create_scope() as cur:
            try:
                cur.execute(q)
                return cur.fetchall()
            except Exception as e:
                print(f"Error lycee no pharmacie: {e}")
                
    # 3.2
    def get_service_profile(self):
        filtered_tables = self.get_all_filtered_tables()
        all_res = list()
        
        for table in filtered_tables:
            
            # q = f"""
            # WITH count_etab AS (
            #     SELECT '{table}' AS table_name, c.code_departement, c.insee_code, c.name AS commune_name, COUNT(t.*) AS total_etab
            #     FROM commune AS c
            #     LEFT JOIN {table} AS t ON c.insee_code = t.insee_code
            #     GROUP BY c.code_departement, c.insee_code
            # )
            
            # SELECT ce.total_etab AS nb_total, ce.table_name AS etab_type, ce.commune_name
            # FROM count_etab AS ce
            # GROUP BY ce.commune_name, ce.total_etab, ce.table_name
            # HAVING ce.total_etab > 0
            # """
            
            q1 = f"""
                SELECT '{table}' AS table_name, c.insee_code, c.name AS commune_name, COUNT(t.*) AS total_etab
                FROM commune AS c
                LEFT JOIN {table} AS t ON c.insee_code = t.insee_code
                GROUP BY c.name, table_name, c.insee_code
                HAVING COUNT(t.*) > 0
            """
            with self._create_scope() as cur:
                try:
                    cur.execute(q1)
                    all_res.extend(cur.fetchall())
                except Exception as e:
                    print(f"Error service profile: {e}")
                    
        return all_res
    
    # def get_pop_and_service(self):
    #     filtered_tables = self.get_all_filtered_tables()
        
    #     query = list()
    #     for table in filtered_tables:
            
    #         match table:
    #             case 'dechets_radioactifs':
    #                 select = "nom_du_site"
    #             case 'clubs_boxe_thai':
    #                 select = "id::text"
    #             case _:
    #                 select = "name"
            
    #         query.append(f"SELECT COUNT({select}) as total, insee_code, '{table}' AS table_name FROM {table} GROUP BY insee_code\n")
            
    #     union = "UNION ALL\n".join(query)
        
    #     q = f"""
    #     WITH count_all AS (
    #         SELECT s.table_name, c.name, c.population, s.insee_code, s.total
    #         FROM commune AS c
    #         LEFT JOIN ({union}) AS s ON c.insee_code = s.insee_code
    #         GROUP BY c.name, s.insee_code, c.population, s.total, s.table_name
    #     )
        
    #     SELECT ca.table_name, NULLIF(ca.total, 0) / NULLIF(ca.population, 0) AS ratio FROM count_all AS ca;
    #     """
        
    #     with self._create_scope() as cur:
    #         try:
    #             cur.execute(q)
    #             res = cur.fetchall()
    #         except Exception as e:
    #             print(f"Error weird request: {e}")
                
    #     for r in res:
    #         if isinstance(r[1], int):
    #             if r[1] > 0:
    #                 print(r)
        
    # 3.3
    def get_pop_and_service_v2(self) -> list:
        filtered_tables = self.get_all_filtered_tables()
        
        query = list()
        for table in filtered_tables:
            select = self.get_primary_key(table)
            
            query.append(f"SELECT insee_code, COUNT({select}) AS nbr FROM {table} GROUP BY insee_code")
            
        union = "\nUNION ALL\n".join(query)
        
        q = f"""
        WITH total_service_commune AS (
            SELECT u.insee_code, SUM(u.nbr) AS total_services
            FROM ({union}) AS u
            GROUP BY u.insee_code
        )
        
        SELECT c.name AS commune_name, c.population,
            COALESCE(s.total_services, 0) AS total_services,
            ROUND( (COALESCE(s.total_services, 0)::numeric / NULLIF(c.population, 0)) * 10000, 2) AS services_for_10k
        FROM commune AS c
        LEFT JOIN total_service_commune AS s ON c.insee_code = s.insee_code
        ORDER BY services_for_10k ASC
        LIMIT 10
        ;
        """
        
        with self._create_scope() as cur:
            try:
                cur.execute(q)
                return cur.fetchall()
            except Exception as e:
                print(f"Error weird request: {e}")
                return []
        
    # 4.1
    def get_nb_hab_per_pharma_per_dept(self):
        q = """
        SELECT ROUND(c.population / COALESCE(COUNT(finess), 0), 2) AS hab_per_pharmacie, d.name
        FROM pharmacie AS p
        INNER JOIN commune AS c ON p.insee_code = c.insee_code
        INNER JOIN departement AS d ON c.code_departement = d.code_departement
        GROUP BY d.name, c.population
        """
        
        with self._create_scope() as cur:
            try:
                cur.execute(q)
                return cur.fetchall()
            except Exception as e:
                print(f"Error weird request: {e}")
                return []
        
    # 4.2
    def get_borrowers(self):
        q = """
        SELECT b.name, ROUND(c.population / NULLIF(b.borrowers, 0), 2) FROM bibliotheque AS b
        INNER JOIN commune AS c ON b.insee_code = c.insee_code
        WHERE borrowers IS NOT NULL
        """
        
        with self._create_scope() as cur:
            try:
                cur.execute(q)
                print(cur.fetchall())
            except Exception as e:
                print(f"Error weird request: {e}")
                return []
        
    # 4.3
    def get_dept_by_service_density(self):
        filtered_tables = self.get_all_filtered_tables()
        all_res = list()
        
        for table in filtered_tables:
            pk = self.get_primary_key(table)
            q = f"""
            WITH total_services AS (
                SELECT t.insee_code, SUM(t.nbr) AS total_service 
                FROM (
                    SELECT insee_code, COUNT({pk}) as nbr FROM {table} GROUP BY insee_code
                ) AS t
                GROUP BY t.insee_code
            )

            SELECT d.name AS dept_name, '{table}' as table_name,
                ROUND( (COALESCE(s.total_service, 0)::numeric / NULLIF(c.population, 0)) * 10000, 2) AS services_for_10k
            FROM commune AS c
            LEFT JOIN total_services AS s ON c.insee_code = s.insee_code
            INNER JOIN departement AS d ON c.code_departement = d.code_departement
            WHERE c.population > 0
            GROUP BY d.name, s.total_service, c.population
            ORDER BY services_for_10k DESC
            LIMIT 10;
            """
            
            with self._create_scope() as cur:
                try:
                    cur.execute(q)
                    all_res.append(cur.fetchall())
                except Exception as e:
                    print(f"Error dept by service: {e}")
                    continue
        return all_res
    
    
    # Bonus
    def get_top_by_group(self):
        filtered_tables = self.get_all_filtered_tables()
        query = list()
        
        for table in filtered_tables:
            select = self.get_primary_key(table)
            query.append(f"SELECT '{table}' AS service, insee_code, COUNT({select}) AS nbr FROM {table} GROUP BY insee_code")
            
        union = "\nUNION ALL\n".join(query)
        
        print(union)
        
        q = f"""
        WITH total_service_commune AS (
            SELECT u.insee_code, u.service, SUM(u.nbr) AS total_services
            FROM ({union}) AS u
            GROUP BY u.insee_code, u.service
        ),
        ranked_communes AS (
            SELECT d.name AS dept_name, c.nom AS commune_name, s.service AS service_name,
                ROUND((COALESCE(s.total_services, 0)::numeric / NULLIF(c.population, 0)) * 10000, 2) AS services_for_10k,
                ROW_NUMBER() OVER(
                    PARTITION BY d.code_departement 
                    ORDER BY (COALESCE(s.total_services, 0)::numeric / NULLIF(c.population, 0)) DESC
        ) AS rn
        FROM commune AS c
        LEFT JOIN total_service_commune AS s ON c.insee_code = s.insee_code
        INNER JOIN departement AS d ON c.code_departement = d.code_departement
        WHERE c.population > 0
        )
        
        SELECT d.name AS dept_name, '{table}' as table_name,
            ROUND( (COALESCE(s.total_services, 0)::numeric / NULLIF(c.population, 0)) * 10000, 2) 
            OVER(PARTITION BY insee_code) AS services_for_10k
        FROM commune AS c
        LEFT JOIN total_service_commune AS s ON c.insee_code = s.insee_code
        INNER JOIN departement AS d ON c.code_departement = d.code_departement
        WHERE c.population > 0
        GROUP BY d.name, s.total_services, c.population, u.service
        ORDER BY services_for_10k DESC
        LIMIT 10;
        """
        # with self._create_scope() as cur:
        #     try:
        #         cur.execute(q)
        #         print(cur.fetchall())
        #     except Exception as e:
        #         print(f"Error dept by service: {e}")

analytic = Analytic()
# analytic.get_mean_etab_by_commune_in_dept()
print(analytic.get_top_by_group())