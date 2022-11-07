class Roster {
    constructor(player_data) {
        this.all_players = []
        player_data.forEach(player => {
            let aPlayer = new Player(player.name, player.team, player.index, player.score, player.goals)
            this.all_players.push(aPlayer)
        })
    }

    getTeam(color) {
        let team_number = 1
        if (color === "Orange") {
            team_number = 2
        }
        let team = []
        this.all_players.forEach(player => {
            if (player.team === team_number) {
                team.push(player)
            }
        })
        return team
    }

    getTeamGoals(color) {
        let team = this.getTeam(color)
        let team_score = 0
        team.forEach(player => {
            team_score += player.goals
        })
        return team_score
    }
}

class Player {
    constructor(name, team, index, score, goals) {
        this.name = name
        this.team = team
        this.index = index
        this.score = score
        this.goals = goals
    }
}