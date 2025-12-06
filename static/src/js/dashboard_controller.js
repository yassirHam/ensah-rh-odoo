/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useRPC } from "@web/core/rpc_service";
import { useState, onMounted } from "@odoo/owl";
import { Component } from "@odoo/owl";

export class DashboardController extends Component {
    static template = "DependatHRDashboard";

    setup() {
        this.rpc = useRPC();
        this.state = useState({
            dashboard_data: null,
            loading: true,
            error: null,
        });
        
        onMounted(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        try {
            this.state.loading = true;
            const result = await this.rpc("/web/dataset/call_kw", {
                model: 'ensa.dashboard',
                method: 'get_dashboard_data',
                args: [],
                kwargs: {},
            });
            this.state.dashboard_data = result;
            this.state.error = null;
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.state.error = error.message || 'Failed to load dashboard data';
            this.state.dashboard_data = {
                employee_stats: { total: 0, by_department: {}, by_skill_level: {} },
                evaluation_stats: { total: 0, avg_score: 0, distribution: {} },
                equipment_stats: { total: 0, by_status: {} },
                training_stats: { total: 0, by_category: {}, avg_score: 0, upcoming: 0 },
                department_distribution: []
            };
        } finally {
            this.state.loading = false;
        }
    }
}

registry.category("actions").add("ensa_dashboard", DashboardController);