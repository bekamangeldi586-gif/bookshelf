class SimpleBarChart {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) throw new Error(`Canvas with id "${canvasId}" not found`);
    
    this.ctx = this.canvas.getContext('2d');
    this.dpr = window.devicePixelRatio || 1;
    
    this.options = {
      padding: 40,
      barColor: '#3682eb',
      textColor: '#333',
      gridColor: '#eee',
      fontSize: 12,
      barGap: 10,
      ...options
    };
    
    const rect = this.canvas.getBoundingClientRect();
    this.canvas.width = rect.width * this.dpr;
    this.canvas.height = rect.height * this.dpr;
    this.ctx.scale(this.dpr, this.dpr);
    
    this.width = rect.width;
    this.height = rect.height;
  }

  draw(data, labels, title = '', yLabel = '', xLabel = '') {
    if (!data || data.length === 0) {
      this.drawError('No data provided');
      return;
    }

    const max = Math.max(...data);
    const min = Math.min(...data, 0);
    const range = max - min || 1;
    const yPadding = range * 0.1;
    const yMax = max + yPadding;
    const yMin = Math.min(min, 0);

    const chartLeft = this.options.padding + 30;
    const chartRight = this.width - this.options.padding;
    const chartTop = this.options.padding;
    const chartBottom = this.height - this.options.padding - 30;

    const chartWidth = chartRight - chartLeft;
    const chartHeight = chartBottom - chartTop;

    this.ctx.fillStyle = '#fff';
    this.ctx.fillRect(0, 0, this.width, this.height);

    this.drawGrid(chartLeft, chartTop, chartWidth, chartHeight, yMin, yMax);
    this.drawAxes(chartLeft, chartTop, chartWidth, chartHeight, yMin, yMax, labels, xLabel, yLabel);

    if (title) this.drawTitle(title);

    const barWidth = (chartWidth - (data.length - 1) * this.options.barGap) / data.length;
    data.forEach((value, i) => {
      const x = chartLeft + i * (barWidth + this.options.barGap);
      const yNorm = (value - yMin) / (yMax - yMin);
      const barHeight = yNorm * chartHeight;
      const y = chartBottom - barHeight;

      this.ctx.fillStyle = this.options.barColor;
      this.ctx.fillRect(x, y, barWidth, barHeight);

      this.ctx.fillStyle = this.options.textColor;
      this.ctx.font = `${this.options.fontSize}px Arial`;
      this.ctx.textAlign = 'center';
      this.ctx.fillText(value, x + barWidth / 2, y - 5);
    });
  }

  drawGrid(left, top, width, height, yMin, yMax) {
    const range = yMax - yMin;
    const steps = 5;
    const step = range / steps;

    this.ctx.strokeStyle = this.options.gridColor;
    this.ctx.lineWidth = 1;

    for (let i = 0; i <= steps; i++) {
      const y = top + (height / steps) * (steps - i);
      this.ctx.beginPath();
      this.ctx.moveTo(left, y);
      this.ctx.lineTo(left + width, y);
      this.ctx.stroke();
    }
  }

  drawAxes(left, top, width, height, yMin, yMax, labels, xLabel, yLabel) {
    this.ctx.strokeStyle = '#000';
    this.ctx.lineWidth = 2;

    this.ctx.beginPath();
    this.ctx.moveTo(left, top + height);
    this.ctx.lineTo(left + width, top + height);
    this.ctx.stroke();

    this.ctx.beginPath();
    this.ctx.moveTo(left, top);
    this.ctx.lineTo(left, top + height);
    this.ctx.stroke();

    this.ctx.fillStyle = this.options.textColor;
    this.ctx.font = `${this.options.fontSize}px Arial`;
    this.ctx.textAlign = 'right';
    const range = yMax - yMin;
    const steps = 5;
    const step = range / steps;

    for (let i = 0; i <= steps; i++) {
      const value = yMin + step * (steps - i);
      const y = top + (height / steps) * i;
      this.ctx.fillText(Math.round(value), left - 10, y + 4);
    }

    if (yLabel) {
      this.ctx.save();
      this.ctx.translate(10, top + height / 2);
      this.ctx.rotate(-Math.PI / 2);
      this.ctx.textAlign = 'center';
      this.ctx.font = `bold ${this.options.fontSize}px Arial`;
      this.ctx.fillText(yLabel, 0, 0);
      this.ctx.restore();
    }

    this.ctx.textAlign = 'center';
    this.ctx.font = `${this.options.fontSize}px Arial`;
    const barWidth = (width - (labels.length - 1) * this.options.barGap) / labels.length;
    labels.forEach((label, i) => {
      const x = left + i * (barWidth + this.options.barGap) + barWidth / 2;
      const y = top + height + 20;
      this.ctx.fillText(label, x, y);
    });

    if (xLabel) {
      this.ctx.textAlign = 'center';
      this.ctx.font = `bold ${this.options.fontSize}px Arial`;
      this.ctx.fillText(xLabel, left + width / 2, top + height + 45);
    }
  }

  drawTitle(title) {
    this.ctx.fillStyle = this.options.textColor;
    this.ctx.font = 'bold 16px Arial';
    this.ctx.textAlign = 'center';
    this.ctx.fillText(title, this.width / 2, 25);
  }

  drawError(message) {
    this.ctx.fillStyle = '#f00';
    this.ctx.font = '14px Arial';
    this.ctx.textAlign = 'center';
    this.ctx.fillText(message, this.width / 2, this.height / 2);
  }
}
