class UserRow extends React.Component {
    render() {
        return <tr>
            <th>{this.props.id}</th>
            <th>{this.props.name}</th>
            <th>{this.props.is_admin}</th>
        </tr>;
    }
}