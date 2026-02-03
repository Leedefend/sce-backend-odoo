<template>
  <section class="home">
    <div class="hero">
      <h2>智能施工平台</h2>
      <p class="lead">请选择左侧菜单开始工作。我们将把菜单、动作与页面统一进同一套壳。</p>
    </div>

    <div class="cards">
      <article class="card">
        <h3>导航就绪</h3>
        <p>当前菜单树已加载，点击任意子菜单会进入动作解析与页面占位。</p>
      </article>
      <article class="card">
        <h3>动作链路</h3>
        <p>菜单 → 动作 → 视图将统一通过 Resolver 输出结构，便于后续扩展。</p>
      </article>
      <article class="card">
        <h3>错误可视</h3>
        <p>任何错误都会回到 StatusPanel，支持快速定位与重试。</p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.home {
  display: grid;
  gap: 24px;
}

.hero {
  padding: 28px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(47, 58, 95, 0.08), rgba(224, 122, 95, 0.16));
}

.hero h2 {
  margin: 0 0 8px;
  font-size: 28px;
}

.lead {
  margin: 0;
  color: #4b5563;
  max-width: 560px;
}

.cards {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.card {
  background: white;
  padding: 20px;
  border-radius: 14px;
  box-shadow: 0 16px 24px rgba(15, 23, 42, 0.08);
}

.card h3 {
  margin-top: 0;
}
</style>
