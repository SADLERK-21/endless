# Endless

Камерный психологический хоррор на Unreal Engine 5.8. Квартира ночью замкнулась в петлю: выходишь за дверь и снова просыпаешься в кровати, а квартира каждый круг меняется всё сильнее и рассказывает историю, которую герой хочет забыть.

- Дизайн-документ: [Docs/GDD.md](Docs/GDD.md)
- MVP-план: [Docs/MVP_Plan.md](Docs/MVP_Plan.md)

## Сборка

1. Visual Studio 2022 с workload *Game development with C++*.
2. Двойной клик по `Endless.uproject` → согласиться на сборку модулей.

## Как собрать уровень

1. `LoopManager` на пол у кровати: здесь игрок просыпается, лицом по стрелке. В Details заполнить `Stages`.
2. `LoopDoor` во входной двери (открывается на E), `LoopExit` сразу за ней: шаг в него = затемнение и пробуждение.
3. Для каждого изменения квартиры: `Anomaly` с `FirstStage` / `LastStage` и списками `ShowWhenActive` / `HideWhenActive`. Для эскалации — BP-наследник с `OnStageChanged`.
4. Сюжетный предмет: `StoryItem` (E = `CompleteObjective`), положить в `ShowWhenActive` аномалии своего этапа. Рядом `StageHint` — подсказка застрявшему.
5. Свет по этапам: один `StageLighting` с таблицей `Stages`. Скриптовые события: Level Blueprint, `OnStageStarted` / `OnStageRepeated` / `OnFinale`.

Квартира и этапы собираются скриптами через unreal-mcp: `Tools/blockout_apartment.py` (стены, свет, Loop-акторы), затем `Tools/stages_week2.py` (заглушки этапов). Каждый пересобирает только свои папки в Outliner.
