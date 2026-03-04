from django.db import connection

def select_host(vm_cpu, vm_ram):
    with connection.cursor() as cur:
        cur.execute("""
        SELECT h.id::text, h.total_cpu, h.total_ram,
               COALESCE(SUM(vm.cpu),0) AS used_cpu,
               COALESCE(SUM(vm.ram),0) AS used_ram
        FROM infrastructure.hosts h
        LEFT JOIN compute_service.virtual_machines vm
          ON vm.host_id = h.id AND vm.status IN ('CREATING','RUNNING')
        WHERE h.is_active = true
        GROUP BY h.id, h.total_cpu, h.total_ram;
        """)
        rows = cur.fetchall()
    best = None
    best_score = -1
    for row in rows:
        host_id, total_cpu, total_ram, used_cpu, used_ram = row
        avail_cpu = total_cpu - used_cpu
        avail_ram = total_ram - used_ram
        if avail_cpu < vm_cpu or avail_ram < vm_ram:
            continue
        cpu_util = used_cpu / total_cpu if total_cpu else 1
        ram_util = used_ram / total_ram if total_ram else 1
        score = 0.6*(1-cpu_util) + 0.4*(1-ram_util)
        if score > best_score:
            best_score = score
            best = {'id': host_id, 'score': score}
    return best
