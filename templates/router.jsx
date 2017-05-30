var Router = ReactRouter.Router;
var Route = ReactRouter.Route;
var browserHis = ReactRouter.browserHistory;



ReactDOM.render(
    <Router history={browserHis}>
        <Route path="/users" component={Users}/>
        <Route path="/category" component={Category}/>
        <Route path="/product" component={Product}/>
        <Route path="/orders" component={Orders}/>
        <Route path="*" component={NotFound}/>
    </Router>,
    document.getElementById("content")
);