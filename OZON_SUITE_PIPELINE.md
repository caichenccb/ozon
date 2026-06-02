# Ozon Suite Image Pipeline

## 1. 简介

这个脚本是一个面向 Ozon 商品套图生成的多 Agent 原型系统。

它的目标不是只生成一张商品图，而是围绕同一个商品生成一整套风格统一、卖点清晰、信息密度高的 Ozon 风格商品图，包括首图、细节图、尺寸图、功能图、生活方式图和场景图。

整体设计思路是：

```text
商品资料输入
  -> 卖点分析
  -> 文字与版式策略
  -> 套图一致性规范
  -> 多类型视觉 Agent 生成图片方案
  -> 图片生成
  -> 后处理叠加文字和尺寸元素
  -> 输出图片与 JSON 结果
```

Ozon 的商品首图通常不是亚马逊式白底主图，而是更接近俄罗斯电商常见的多信息销售海报：大标题、产品主体、徽章、赠品、数量标识、卖点说明和强视觉背景。因此本系统的 prompt 方向也偏向“多信息素 Ozon marketplace creative”。

## 2. 输入数据

核心输入由 `ProductInput` 定义：

```python
@dataclass
class ProductInput:
    name: str
    category: str = ""
    image_path: str = ""
    dimensions: str = ""
    material: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
```

字段说明：

- `name`：产品名称。
- `category`：产品类别。
- `image_path`：产品参考图路径。用于分析产品外观，也用于图片编辑阶段保持产品一致。
- `dimensions`：尺寸参数。主要用于尺寸图。
- `material`：材质参数。用于卖点分析、细节图和尺寸图信息展示。
- `parameters`：其他扩展参数，比如使用场景、风格、套装数量、赠品信息等。

## 3. 输出结果

每个商品会输出：

- 多张套图图片。
- 每张图对应的 Agent 输出 JSON。
- 每张图的最终 `generation_prompt`。
- 整体策略数据，包括卖点、文字设计、一致性规范。
- 汇总文件：`outputs/full_pipeline.json`。

默认生成 6 类图：

```text
MainInfographicAgent
DetailAgent
DimensionAgent
FeatureAgent
LifestyleAgent
SceneDesignAgent
```

## 4. Agent 总览

系统里的 Agent 分为两类：

1. 策略 Agent：先理解产品，制定统一方向。
2. 视觉 Agent：根据策略生成不同类型图片的设计方案。

### 4.1 BaseAgent

`BaseAgent` 是所有 Agent 的基类。

它负责：

- 保存 Agent 名称和 system prompt。
- 接收 `ProductInput` 和上下文 `context`。
- 如果有产品图片，把图片一并传给模型。
- 调用 OpenAI chat model。
- 要求模型返回 JSON。
- 将模型输出解析成 Python dict。

所有具体 Agent 都继承自它。

## 5. 策略 Agent

### 5.1 SellingPointAgent

职责：卖点分析 Agent。

它负责从产品名称、类别、尺寸、材质、参数和产品图片中提取销售策略。

主要输出内容：

- `core_selling_points`：核心卖点。
- `buyer_pains`：买家痛点。
- `proof_points`：支撑卖点的证明点。
- `visual_priorities`：视觉上最应该强调的内容。
- `tone_ru`：俄语电商文案语气。
- `forbidden_claims`：不应该夸大的宣传点。

它是后续所有 Agent 的基础。后面的文字设计、一致性规范和各类图片设计都会参考它。

### 5.2 TextDesignAgent

职责：文字设计与版式策略 Agent。

它负责设计俄语文案和文字视觉系统。

主要输出内容：

- `text_system`：整体文字系统。
- `main_copy_options_ru`：主标题候选俄语文案。
- `secondary_copy_options_ru`：副标题候选俄语文案。
- `label_style`：标签、徽章、卖点说明的风格。
- `placement_rules`：文字放置规则。
- `no_text_scenes`：哪些图片类型不应该叠加文字。

注意：图片模型不直接生成最终文字。文字由后处理阶段使用 PIL 叠加，这样可以减少俄语乱码、错字和假字问题。

### 5.3 SuiteConsistencyAgent

职责：套图一致性 Agent。

它负责制定整套图片的统一视觉规范，解决测试生图时常见的前后不一致问题。

主要输出内容：

- `product_identity`：产品身份识别，比如形状、结构、核心外观。
- `fixed_visual_traits`：必须固定的视觉特征。
- `color_palette`：统一色彩方案。
- `background_style`：背景风格。
- `lighting_style`：灯光风格。
- `camera_rules`：镜头和角度规则。
- `graphic_system`：统一的徽章、信息块、装饰元素系统。
- `recurring_badges`：整套图中可以重复出现的徽章元素。
- `forbidden_variations`：禁止变化的内容。

它的输出会进入每一张图的 `generation_prompt`，用于约束产品外观、颜色、材质、比例、数量和整体视觉风格。

## 6. 视觉 Agent

所有视觉 Agent 都遵循统一的 `VISUAL_AGENT_CONTRACT`。

这个契约要求它们输出类似下面的 JSON 字段：

```json
{
  "scene_type": "",
  "camera": "",
  "lighting": "",
  "composition": "",
  "main_copy_ru": "",
  "secondary_copy_ru": "",
  "visual_focus": [],
  "negative_prompt": ""
}
```

同时它们都必须遵守：

- Ozon 多信息海报风格。
- 产品主体清晰。
- 信息元素丰富。
- 保留后期叠字空间。
- 不让图片模型直接生成最终俄语文字。
- 遵守 `suite_consistency` 一致性规范。

### 6.1 MainInfographicAgent

职责：Ozon 首图 / 图一 Agent。

它负责生成类似 Ozon/Wildberries 商品首图的高冲击销售海报方案。

适合表现：

- 大产品主体。
- 大标题区域。
- 数量徽章。
- 赠品或 bonus 徽章。
- 多卖点信息块。
- 强对比背景。
- 电商促销感。

它不是白底主图 Agent，而是多信息销售首图 Agent。

### 6.2 DetailAgent

职责：细节图 Agent。

它负责突出产品材质、纹理、结构、做工、局部细节。

适合表现：

- 材质特写。
- 表面纹理。
- 接缝、边缘、工艺。
- 局部卖点放大。
- 质量感和耐用感。

### 6.3 DimensionAgent

职责：尺寸图 Agent。

它负责生成尺寸说明类图片方案，并且会重点使用 `product.dimensions`。

适合表现：

- 尺寸箭头。
- 长宽高说明。
- 与手、手机、桌面等参照物对比。
- 尺寸徽章。
- 材质和规格信息。

代码里还为它做了专门的后处理函数：

```python
render_dimension_overlay(...)
```

该函数会叠加：

- 尺寸徽章。
- 横向测量箭头。
- 纵向测量箭头。
- 尺寸参数。
- 材质参数。

### 6.4 FeatureAgent

职责：功能卖点图 Agent。

它负责把产品功能和利益点转成可视化说明。

适合表现：

- 功能拆解。
- 使用效果。
- 耐用性。
- 便捷性。
- 对比优势。
- 结构说明。

### 6.5 LifestyleAgent

职责：生活方式图 Agent。

它负责把产品放入真实使用场景中，提升买家的代入感。

适合表现：

- 家庭场景。
- 户外场景。
- 办公场景。
- 礼品场景。
- 真实用户使用状态。

### 6.6 SceneDesignAgent

职责：高级场景图 Agent。

它和 `LifestyleAgent` 有相似之处，但更偏整体场景美术设计。

适合表现：

- 高级背景。
- 道具搭配。
- 氛围感。
- 品类相关环境。
- 更完整的视觉主题。

如果 `LifestyleAgent` 更像“真实使用”，那么 `SceneDesignAgent` 更像“精心布置的商业场景”。

## 7. Agent 之间的关联关系

整体关系如下：

```text
ProductInput
  |
  |---> SellingPointAgent
  |       |
  |       v
  |    selling_points
  |
  |---> TextDesignAgent
  |       input: product + selling_points
  |       output: text_design
  |
  |---> SuiteConsistencyAgent
          input: product + selling_points + text_design
          output: suite_consistency

strategy = {
  product,
  selling_points,
  text_design,
  suite_consistency
}

strategy
  |
  |---> MainInfographicAgent
  |---> DetailAgent
  |---> DimensionAgent
  |---> FeatureAgent
  |---> LifestyleAgent
  |---> SceneDesignAgent
          |
          v
      agent_output
          |
          v
      build_generation_prompt()
          |
          v
      generate_image()
          |
          v
      post_process_image()
          |
          v
      final image + JSON
```

简化理解：

```text
SellingPointAgent 决定卖什么
TextDesignAgent 决定怎么写
SuiteConsistencyAgent 决定整套图怎么统一
视觉 Agent 决定每张图怎么画
build_generation_prompt 把策略和单图设计合并成最终 prompt
generate_image 负责出图
post_process_image 负责后期叠字和尺寸元素
```

## 8. Prompt 一致性机制

为了减少套图前后不一致，`build_generation_prompt()` 会把 `suite_consistency` 注入每一张图片 prompt。

关键约束包括：

- 同一个商品形状不能变。
- 颜色不能变。
- 材质不能变。
- 比例不能变。
- 数量和套装印象不能乱。
- 图形语言要统一。
- 背景风格要相关。
- 徽章、文字区域、色彩系统要统一。

negative prompt 也加入了：

```text
inconsistent product
changed color
changed shape
changed material
wrong quantity
different brand style
mismatched background system
misspelled text
fake letters
watermark
```

## 9. 后处理逻辑

当前后处理主要由两个函数完成：

### 9.1 render_title_panel

负责通用标题区域。

它会叠加：

- 主标题。
- 副标题。
- 顶部白色文字面板。

### 9.2 render_dimension_overlay

只对 `DimensionAgent` 生效。

它会叠加：

- 尺寸徽章。
- 横向尺寸箭头。
- 纵向尺寸箭头。
- 尺寸参数。
- 材质信息。

## 10. 当前阶段定位

这个项目目前是 Ozon 套图生成 SaaS 的核心逻辑原型。

已经具备：

- 多 Agent 分工。
- 商品图输入。
- 卖点分析。
- 文字设计。
- 套图一致性控制。
- 多类型图片生成。
- 尺寸图后处理。
- JSON 结果输出。

后续建议继续增强：

- 增加 `QualityCheckAgent`，生成后检查一致性和错误。
- 增加失败重试机制。
- 增加更多模板化后处理布局。
- 增加前端预览和手动调整。
- 增加后端任务队列、用户项目、文件存储和生成记录。
- 增加 Ozon 平台规则检查。
