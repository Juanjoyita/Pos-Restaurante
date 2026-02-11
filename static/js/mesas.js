let estadoPrevio = new Map(); // mesa_id -> estado

function showToast(msg){
  const t = document.getElementById("toast");
  if(!t) return;
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(()=>t.classList.remove("show"), 1400);
}

async function refrescarMesas(){
  try{
    const res = await fetch("/mesas.json", { cache: "no-store" });
    if(!res.ok) return;

    const data = await res.json();
    const mesas = data.mesas || [];

    const grid = document.getElementById("grid-mesas");
    if(!grid) return;

    // construir HTML
    grid.innerHTML = mesas.map(m => {
      const estado = (m.estado || "libre").toLowerCase();
      const pillClass = estado === "ocupada" ? "ocupada" : "libre";
      const label = estado === "ocupada" ? "Ocupada" : "Libre";

      return `
        <div class="card" data-id="${m.id}" data-estado="${estado}">
          <a href="/mesa/${m.id}">
            <div class="num">Mesa ${m.numero}</div>
            <div class="meta">
              <span class="pill ${pillClass}">
                <span class="dot"></span>
                ${label}
              </span>
              <span class="small">Tap para abrir</span>
            </div>
          </a>
        </div>
      `;
    }).join("");

    // detectar cambios de estado y avisar
    for(const m of mesas){
      const prev = estadoPrevio.get(m.id);
      const now = (m.estado || "libre").toLowerCase();
      if(prev && prev !== now){
        showToast(`Mesa ${m.numero}: ${prev} → ${now}`);
      }
      estadoPrevio.set(m.id, now);
    }

  }catch(e){
    console.log("Error refrescando mesas", e);
  }
}

refrescarMesas();
setInterval(refrescarMesas, 2500);
