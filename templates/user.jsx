class UserRow extends React.Component{
    render(){
        return <tr>
            <th>{this.props.id}</th>
            <th>{this.props.name}</th>
            <th>{this.props.is_admin}</th>
        </tr>;
    }
};
class UserTable extends React.Component{
    render(){
        return <Table striped bordered condensed hover>
            <thead>
            <tr>
                <th>ИД</th>
                <th>Имя</th>
                <th>Админ</th>
            </tr>
            </thead>
            <tbody>
            {
                this.props.data.items.map(function (item) {
                    return <UserRow id={item.id} name={item.name} is_admin={item.is_admin}/>
                })
            }
            </tbody>;
    }
}