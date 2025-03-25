// 初始化ECharts实例
const marketOverview = echarts.init(document.getElementById('marketOverview'));
const topList = echarts.init(document.getElementById('topList'));

// 获取市场概览数据
async function fetchMarketOverview() {
    try {
        const response = await fetch('/api/market/market/overview/');
        const data = await response.json();
        
        // 处理市场概览数据
        const marketStats = data.market_stats;
        const option = {
            title: {
                text: '市场资金流向',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            legend: {
                data: ['买入金额', '卖出金额', '净流入'],
                bottom: 10
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: [
                {
                    type: 'category',
                    data: marketStats.map(item => item.stock__market === 'SH' ? '上海' : '深圳')
                }
            ],
            yAxis: [
                {
                    type: 'value',
                    name: '金额（亿元）',
                    axisLabel: {
                        formatter: '{value}'
                    }
                }
            ],
            series: [
                {
                    name: '买入金额',
                    type: 'bar',
                    data: marketStats.map(item => (item.buy_amount / 100000000).toFixed(2)),
                    itemStyle: {
                        color: '#ff7675'
                    }
                },
                {
                    name: '卖出金额',
                    type: 'bar',
                    data: marketStats.map(item => (item.sell_amount / 100000000).toFixed(2)),
                    itemStyle: {
                        color: '#74b9ff'
                    }
                },
                {
                    name: '净流入',
                    type: 'bar',
                    data: marketStats.map(item => (item.net_flow / 100000000).toFixed(2)),
                    itemStyle: {
                        color: '#00b894'
                    }
                }
            ]
        };
        
        marketOverview.setOption(option);
    } catch (error) {
        console.error('获取市场概览数据失败:', error);
    }
}

// 获取龙虎榜TOP5数据
async function fetchTopList() {
    try {
        const response = await fetch('/api/market/top-list/');
        const data = await response.json();
        
        // 处理龙虎榜数据
        const topLists = data.top_lists.slice(0, 5);
        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'value',
                position: 'top',
                splitLine: {
                    lineStyle: {
                        type: 'dashed'
                    }
                }
            },
            yAxis: {
                type: 'category',
                axisLine: { show: false },
                axisLabel: { show: true },
                axisTick: { show: false },
                splitLine: { show: false },
                data: topLists.map(item => item.stock__name)
            },
            series: [
                {
                    name: '净额',
                    type: 'bar',
                    data: topLists.map(item => (item.net_amount / 10000).toFixed(2)),
                    label: {
                        show: true,
                        formatter: '{c} 万'
                    },
                    itemStyle: {
                        color: function(params) {
                            return params.data >= 0 ? '#ff7675' : '#74b9ff';
                        }
                    }
                }
            ]
        };
        
        topList.setOption(option);
    } catch (error) {
        console.error('获取龙虎榜数据失败:', error);
    }
}

// 初始化页面数据
fetchMarketOverview();
fetchTopList();

// 处理窗口大小变化
window.addEventListener('resize', function() {
    marketOverview.resize();
    topList.resize();
});

// 用户登录状态管理
const token = localStorage.getItem('token');
if (token) {
    // 更新导航栏显示
    document.getElementById('userNav').innerHTML = `
        <a class="nav-link" href="/user/profile">个人中心</a>
        <a class="nav-link" href="#" onclick="logout()">退出</a>
    `;
    
    // 检查VIP状态
    fetch('/api/users/subscription/status/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.is_vip) {
            // 启用VIP功能
            enableVipFeatures();
        }
    })
    .catch(error => console.error('获取订阅状态失败:', error));
}

// 启用VIP功能
function enableVipFeatures() {
    // 添加高级筛选选项
    const filterOptions = document.createElement('div');
    filterOptions.className = 'vip-filters mt-3';
    filterOptions.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <select class="form-select" id="traderFilter">
                    <option value="">按游资筛选</option>
                </select>
            </div>
            <div class="col-md-4">
                <select class="form-select" id="dateRangeFilter">
                    <option value="7">最近7天</option>
                    <option value="30">最近30天</option>
                    <option value="90">最近90天</option>
                </select>
            </div>
            <div class="col-md-4">
                <button class="btn btn-primary" onclick="applyFilters()">应用筛选</button>
            </div>
        </div>
    `;
    
    document.querySelector('.card-body').appendChild(filterOptions);
}

// 退出登录
function logout() {
    localStorage.removeItem('token');
    window.location.href = '/';
}

// 订阅处理
const subscribeButtons = document.querySelectorAll('.pricing-card button');
subscribeButtons.forEach(button => {
    button.addEventListener('click', function() {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/user/login';
            return;
        }
        
        const type = this.closest('.pricing-card').querySelector('h3').textContent.toLowerCase();
        const subscriptionType = type.includes('月度') ? 'monthly' :
                               type.includes('季度') ? 'quarterly' : 'yearly';
        
        // 模拟支付流程
        const paymentId = 'PAY' + Date.now();
        
        // 创建订阅
        fetch('/api/users/subscribe/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `Bearer ${token}`
            },
            body: `subscription_type=${subscriptionType}&payment_id=${paymentId}`
        })
        .then(response => response.json())
        .then(data => {
            alert('订阅成功！');
            location.reload();
        })
        .catch(error => {
            console.error('订阅失败:', error);
            alert('订阅失败，请稍后重试');
        });
    });
});